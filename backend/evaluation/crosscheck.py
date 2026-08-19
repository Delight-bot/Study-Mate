"""
Feature #4: Hallucination Checker
Cross-checks LLM responses to detect inconsistencies and potential hallucinations
"""

from typing import Dict, List, Tuple
import re
from difflib import SequenceMatcher

class HallucinationChecker:
    """Detects potential hallucinations by cross-checking LLM responses"""

    def __init__(self):
        self.similarity_threshold = 0.3  # Minimum similarity to consider responses related
        self.inconsistency_threshold = 0.5  # Threshold for flagging inconsistencies

    def extract_facts(self, text: str) -> List[str]:
        """
        Extract factual statements from text

        This is a simplified version - in production you'd use NLP
        """
        # Split into sentences
        sentences = re.split(r'[.!?]+', text)

        facts = []
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:  # Ignore very short sentences
                # Filter out opinion/uncertainty markers
                uncertainty_markers = ['might', 'could', 'possibly', 'maybe', 'perhaps', 'likely']
                if not any(marker in sentence.lower() for marker in uncertainty_markers):
                    facts.append(sentence)

        return facts

    def extract_numbers(self, text: str) -> List[Tuple[str, float]]:
        """
        Extract numerical claims from text

        Returns:
            List of tuples (context, number)
        """
        # Find numbers in context
        pattern = r'([^.]*?)(\d+\.?\d*)\s*(%|percent|degrees?|years?|[a-zA-Z]+)?'
        matches = re.findall(pattern, text)

        numbers = []
        for context, number, unit in matches:
            try:
                value = float(number)
                context_clean = context.strip()[-30:]  # Last 30 chars for context
                numbers.append((context_clean + " " + unit, value))
            except ValueError:
                continue

        return numbers

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts (0.0 to 1.0)"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

    def check_numerical_consistency(
        self,
        responses: Dict[str, str]
    ) -> Dict[str, List[Dict]]:
        """
        Check if numerical values are consistent across responses

        Returns:
            Dict of inconsistencies found
        """
        inconsistencies = {}

        # Extract numbers from each response
        all_numbers = {}
        for llm_name, response in responses.items():
            all_numbers[llm_name] = self.extract_numbers(response)

        # Compare numerical values
        llm_names = list(responses.keys())
        for i, llm1 in enumerate(llm_names):
            for llm2 in llm_names[i + 1:]:
                numbers1 = all_numbers[llm1]
                numbers2 = all_numbers[llm2]

                # Check if they have similar contexts but different numbers
                for ctx1, num1 in numbers1:
                    for ctx2, num2 in numbers2:
                        # If contexts are similar
                        similarity = self.calculate_similarity(ctx1, ctx2)
                        if similarity > 0.3:
                            # But numbers differ significantly
                            if abs(num1 - num2) / max(abs(num1), abs(num2), 1) > 0.1:
                                key = f"{llm1}_vs_{llm2}"
                                if key not in inconsistencies:
                                    inconsistencies[key] = []

                                inconsistencies[key].append({
                                    'type': 'numerical',
                                    'llm1': llm1,
                                    'llm2': llm2,
                                    'context': ctx1,
                                    'value1': num1,
                                    'value2': num2,
                                    'difference': abs(num1 - num2)
                                })

        return inconsistencies

    def check_factual_consistency(
        self,
        responses: Dict[str, str]
    ) -> Dict[str, List[Dict]]:
        """
        Check for contradicting factual statements

        Returns:
            Dict of potential contradictions
        """
        contradictions = {}

        # Extract facts from each response
        all_facts = {}
        for llm_name, response in responses.items():
            all_facts[llm_name] = self.extract_facts(response)

        # Look for contradictions
        # This is simplified - in production, use NLP to detect semantic contradictions
        llm_names = list(responses.keys())

        # Check for negation patterns
        negation_patterns = [
            (r'\bnot\b', r'\bis\b'),
            (r'\bno\b', r'\byes\b'),
            (r'\btrue\b', r'\bfalse\b'),
            (r'\bcorrect\b', r'\bincorrect\b'),
        ]

        for i, llm1 in enumerate(llm_names):
            for llm2 in llm_names[i + 1:]:
                facts1 = all_facts[llm1]
                facts2 = all_facts[llm2]

                for fact1 in facts1:
                    for fact2 in facts2:
                        # If the sentences are similar but have opposing terms
                        similarity = self.calculate_similarity(fact1, fact2)

                        if 0.3 < similarity < 0.9:  # Similar but not identical
                            # Check for negation patterns
                            has_contradiction = False
                            for neg, pos in negation_patterns:
                                if re.search(neg, fact1.lower()) and re.search(pos, fact2.lower()):
                                    has_contradiction = True
                                    break
                                elif re.search(pos, fact1.lower()) and re.search(neg, fact2.lower()):
                                    has_contradiction = True
                                    break

                            if has_contradiction:
                                key = f"{llm1}_vs_{llm2}"
                                if key not in contradictions:
                                    contradictions[key] = []

                                contradictions[key].append({
                                    'type': 'factual',
                                    'llm1': llm1,
                                    'llm2': llm2,
                                    'statement1': fact1,
                                    'statement2': fact2,
                                    'similarity': round(similarity, 3)
                                })

        return contradictions

    def calculate_consensus(self, responses: Dict[str, str]) -> Dict[str, float]:
        """
        Calculate how much consensus there is between responses

        Returns:
            Dict mapping each LLM to a consensus score (0.0 to 1.0)
        """
        consensus_scores = {}
        llm_names = list(responses.keys())

        for llm1 in llm_names:
            similarities = []
            for llm2 in llm_names:
                if llm1 != llm2:
                    similarity = self.calculate_similarity(
                        responses[llm1],
                        responses[llm2]
                    )
                    similarities.append(similarity)

            # Average similarity with other responses
            consensus_scores[llm1] = sum(similarities) / len(similarities) if similarities else 0.0

        return consensus_scores

    def detect_hallucinations(
        self,
        responses: Dict[str, str],
        question: str = ""
    ) -> Dict[str, any]:
        """
        Main method to detect potential hallucinations

        Returns:
            Comprehensive report on inconsistencies and hallucinations
        """
        # Check numerical consistency
        numerical_issues = self.check_numerical_consistency(responses)

        # Check factual consistency
        factual_issues = self.check_factual_consistency(responses)

        # Calculate consensus
        consensus = self.calculate_consensus(responses)

        # Identify outliers (potential hallucinations)
        avg_consensus = sum(consensus.values()) / len(consensus) if consensus else 0
        outliers = {
            llm: score
            for llm, score in consensus.items()
            if score < avg_consensus - 0.15
        }

        # Calculate overall inconsistency score
        total_issues = (
            sum(len(issues) for issues in numerical_issues.values()) +
            sum(len(issues) for issues in factual_issues.values())
        )

        inconsistency_score = min(1.0, total_issues * 0.1)

        # Flag potential hallucinations
        flagged_llms = []
        for llm in outliers:
            if consensus[llm] < 0.4:  # Low consensus with others
                flagged_llms.append(llm)

        report = {
            'inconsistency_score': round(inconsistency_score, 3),
            'numerical_issues': numerical_issues,
            'factual_issues': factual_issues,
            'consensus_scores': {k: round(v, 3) for k, v in consensus.items()},
            'outliers': outliers,
            'flagged_llms': flagged_llms,
            'has_major_issues': inconsistency_score > 0.3 or len(flagged_llms) > 0,
            'recommendation': self._generate_recommendation(
                inconsistency_score,
                flagged_llms,
                consensus
            )
        }

        return report

    def _generate_recommendation(
        self,
        inconsistency_score: float,
        flagged_llms: List[str],
        consensus: Dict[str, float]
    ) -> str:
        """Generate a recommendation based on the analysis"""
        if inconsistency_score < 0.2 and not flagged_llms:
            return "All responses show good consistency. No major concerns detected."

        if flagged_llms:
            most_reliable = max(consensus, key=consensus.get)
            return (
                f"Inconsistencies detected. The following LLMs may have hallucinated: "
                f"{', '.join(flagged_llms)}. Consider trusting {most_reliable} "
                f"(consensus score: {consensus[most_reliable]:.2f})"
            )

        return (
            f"Some inconsistencies found (score: {inconsistency_score:.2f}). "
            "Review responses carefully and verify facts independently."
        )
