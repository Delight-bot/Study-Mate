"""
LangGraph pipeline behind POST /api/chat/ask

    prepare ──Send×N──▶ call_llm ──▶ persist ──▶ evaluate ──▶ fuse ──▶ END
                                                     └───(<2 answers)───▶ END

prepare   resolves the room's subject_id, detects subject (if none given) and
          difficulty, and builds one optimized prompt per configured LLM.
call_llm  runs once per LLM in parallel (fan-out via Send); each call is
          time-bounded and failures are captured as error entries.
persist   stores successful answers in llm_responses.
evaluate  heuristic scoring + cross-model consistency check.
fuse      stitches the best sections of each answer together.
"""

import asyncio
import operator
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from database import execute_query, execute_update
from evaluation import DifficultyDetector, HallucinationChecker, ResponseFusionEngine, ResponseScorer
from memory import SubjectClassifier
from services import PromptOptimizer

# A single slow/misbehaving provider must not block the whole comparison
# indefinitely — cap each call and let the others still come back.
# (The deprecated google-generativeai SDK has been observed to hang
# indefinitely when run concurrently with another async call in the same
# event loop, rather than erroring quickly — this bound exists specifically
# to contain that, but applies to any provider.)
LLM_TIMEOUT_SECONDS = 30

prompt_optimizer = PromptOptimizer()
subject_classifier = SubjectClassifier()
difficulty_detector = DifficultyDetector()
scorer = ResponseScorer()
hallucination_checker = HallucinationChecker()
fusion_engine = ResponseFusionEngine()


class AskState(TypedDict, total=False):
    # inputs
    user_id: int
    question: str
    subject: Optional[str]
    # set by prepare
    subject_id: Optional[int]
    detected_subject: Optional[str]
    difficulty: Optional[str]
    prompts: dict[str, str]
    # appended to concurrently by the call_llm branches
    responses: Annotated[list[dict], operator.add]
    # set by evaluate / fuse
    evaluation: Optional[dict]
    fused: Optional[dict]


class CallState(TypedDict):
    llm_name: str
    prompt: str


def build_ask_graph(llm_services: dict[str, Any]):
    """Compile the ask pipeline for the given {llm_name: service} map."""

    async def prepare(state: AskState) -> dict:
        subject = state.get("subject")
        subject_id = None
        detected_subject = None

        if subject:
            result = await execute_query("SELECT id FROM subjects WHERE name = ?", (subject,))
            if result:
                subject_id = result[0]["id"]
        else:
            # Only used to steer the prompt — the answer isn't filed under a
            # room the user didn't pick.
            detected, _, _ = subject_classifier.classify(state["question"])
            if detected != "General":
                detected_subject = detected

        difficulty, _, _ = difficulty_detector.classify_difficulty(state["question"])

        prompts = {
            llm_name: prompt_optimizer.optimize_prompt(
                question=state["question"],
                llm_name=llm_name,
                subject=subject or detected_subject,
                difficulty=difficulty,
            )
            for llm_name in llm_services
        }

        return {
            "subject_id": subject_id,
            "detected_subject": detected_subject,
            "difficulty": difficulty,
            "prompts": prompts,
        }

    def fan_out(state: AskState) -> list[Send]:
        return [
            Send("call_llm", {"llm_name": llm_name, "prompt": prompt})
            for llm_name, prompt in state["prompts"].items()
        ]

    async def call_llm(state: CallState) -> dict:
        llm_name = state["llm_name"]
        try:
            result = await asyncio.wait_for(
                llm_services[llm_name].timed_generate(state["prompt"]),
                timeout=LLM_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            # str(asyncio.TimeoutError()) == "", so give it a readable message.
            return {"responses": [_error_entry(llm_name, f"timed out after {LLM_TIMEOUT_SECONDS}s")]}
        except Exception as e:
            return {"responses": [_error_entry(llm_name, str(e))]}

        return {"responses": [{
            "llm_name": llm_name,
            "response_text": result.get("response_text", ""),
            "response_time": result.get("response_time", 0),
            "token_count": result.get("token_count"),
            "model": result.get("model"),
        }]}

    async def persist(state: AskState) -> dict:
        for resp in state["responses"]:
            if resp.get("error"):
                continue
            await execute_update(
                """INSERT INTO llm_responses
                   (user_id, question, subject_id, llm_name, response_text, response_time, token_count, prompt_used)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    state["user_id"],
                    state["question"],
                    state.get("subject_id"),
                    resp["llm_name"],
                    resp["response_text"],
                    resp["response_time"],
                    resp.get("token_count"),
                    state["prompts"][resp["llm_name"]],
                ),
            )
        return {}

    async def evaluate(state: AskState) -> dict:
        answers = _successful_answers(state)
        if not answers:
            return {"evaluation": None}

        comparison = scorer.compare_responses(answers, state["question"])
        evaluation = {
            "scores": comparison["scores"],
            "ranking": comparison["ranking"],
            "best": comparison["best"],
        }
        if len(answers) >= 2:
            check = hallucination_checker.detect_hallucinations(answers, state["question"])
            evaluation["consistency"] = {
                "consensus_scores": check["consensus_scores"],
                "flagged_llms": check["flagged_llms"],
                "has_major_issues": check["has_major_issues"],
                "recommendation": check["recommendation"],
            }
        return {"evaluation": evaluation}

    def should_fuse(state: AskState) -> str:
        return "fuse" if len(_successful_answers(state)) >= 2 else END

    async def fuse(state: AskState) -> dict:
        answers = _successful_answers(state)
        scores = (state.get("evaluation") or {}).get("scores")
        fused = fusion_engine.fuse_responses(answers, scores)
        if not fused["fused_response"].strip():
            return {"fused": None}
        return {"fused": {
            "response_text": fused["fused_response"],
            "attribution": fused["attribution"],
            "llms_contributed": fused["llms_contributed"],
        }}

    graph = StateGraph(AskState)
    graph.add_node("prepare", prepare)
    graph.add_node("call_llm", call_llm)
    graph.add_node("persist", persist)
    graph.add_node("evaluate", evaluate)
    graph.add_node("fuse", fuse)

    graph.add_edge(START, "prepare")
    graph.add_conditional_edges("prepare", fan_out, ["call_llm"])
    graph.add_edge("call_llm", "persist")
    graph.add_edge("persist", "evaluate")
    graph.add_conditional_edges("evaluate", should_fuse, ["fuse", END])
    graph.add_edge("fuse", END)

    return graph.compile()


def _error_entry(llm_name: str, message: str) -> dict:
    return {
        "llm_name": llm_name,
        "response_text": f"Error: {message}",
        "response_time": 0,
        "error": True,
    }


def _successful_answers(state: AskState) -> dict[str, str]:
    return {
        r["llm_name"]: r["response_text"]
        for r in state.get("responses", [])
        if not r.get("error") and r.get("response_text")
    }
