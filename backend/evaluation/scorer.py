"""
Feature #2: Automatic Scoring System
Evaluates LLM responses based on multiple metrics
"""

from typing import Dict
import re

class ResponseScorer:
    """Scores LLM responses on various quality metrics"""

    def __init__(self):
        self.weights = {
            'clarity': 0.25,
            'depth': 0.30,
            'formatting': 0.20,
            'correctness': 0.25
        }

    def score_clarity(self, response: str) -> float:
        """
        Score response clarity (0.0 to 1.0)

        Factors:
        - Sentence structure
        - Use of transition words
        - Paragraph organization
        - Readability
        """
        score = 0.5  # Base score

        # Check for complete sentences
        sentences = re.split(r'[.!?]+', response)
        valid_sentences = [s for s in sentences if len(s.strip()) > 10]
        if len(valid_sentences) >= 3:
            score += 0.15

        # Check for transition words
        transition_words = ['however', 'therefore', 'additionally', 'furthermore', 'moreover', 'thus', 'hence']
        if any(word in response.lower() for word in transition_words):
            score += 0.1

        # Check for clear structure (paragraphs)
        paragraphs = response.split('\n\n')
        if len(paragraphs) > 1:
            score += 0.15

        # Penalize if too short
        if len(response) < 50:
            score -= 0.2

        # Check readability (average sentence length)
        if valid_sentences:
            avg_sentence_length = len(response) / len(valid_sentences)
            if 50 < avg_sentence_length < 200:
                score += 0.1

        return max(0.0, min(1.0, score))

    def score_depth(self, response: str, question: str = "") -> float:
        """
        Score response depth and thoroughness (0.0 to 1.0)

        Factors:
        - Length
        - Technical detail
        - Examples provided
        - Explanations
        """
        score = 0.3  # Base score

        # Length factor
        if len(response) > 200:
            score += 0.2
        if len(response) > 500:
            score += 0.1

        # Check for examples
        example_indicators = ['for example', 'for instance', 'such as', 'e.g.', 'like']
        if any(indicator in response.lower() for indicator in example_indicators):
            score += 0.15

        # Check for explanations
        explanation_indicators = ['because', 'since', 'due to', 'as a result', 'this means']
        if any(indicator in response.lower() for indicator in explanation_indicators):
            score += 0.15

        # Check for technical terms (rough heuristic)
        technical_markers = re.findall(r'\b[A-Z]{2,}\b|\b\w+[A-Z]\w*\b', response)
        if len(technical_markers) > 2:
            score += 0.1

        return max(0.0, min(1.0, score))

    def score_formatting(self, response: str) -> float:
        """
        Score response formatting (0.0 to 1.0)

        Factors:
        - Use of bullet points/lists
        - Code blocks
        - Headers
        - Bold/italic text
        """
        score = 0.5  # Base score

        # Check for lists/bullet points
        if re.search(r'^\s*[-*•]\s', response, re.MULTILINE):
            score += 0.15

        # Check for numbered lists
        if re.search(r'^\s*\d+\.\s', response, re.MULTILINE):
            score += 0.15

        # Check for code blocks
        if '```' in response or '`' in response:
            score += 0.1

        # Check for headers
        if re.search(r'^#{1,6}\s', response, re.MULTILINE):
            score += 0.1

        return max(0.0, min(1.0, score))

    def score_correctness(self, response: str, question: str = "", reference: str = None) -> float:
        """
        Score response correctness (0.0 to 1.0)

        This is a placeholder - in production, you'd use:
        - Fact-checking APIs
        - Reference comparisons
        - Domain-specific validators
        """
        score = 0.7  # Default assumption of correctness

        # Check for uncertainty markers (good!)
        uncertainty = ['might', 'could be', 'possibly', 'likely', 'probably', 'uncertain']
        if any(word in response.lower() for word in uncertainty):
            score += 0.05  # Reward appropriate uncertainty

        # Check for absolute claims without evidence (bad)
        absolute_claims = ['always', 'never', 'definitely', 'certainly', 'absolutely']
        absolute_count = sum(1 for word in absolute_claims if word in response.lower())
        if absolute_count > 2:
            score -= 0.1  # Penalize overconfident claims

        # If reference is provided, do basic comparison
        if reference:
            # Simple keyword overlap check
            response_words = set(response.lower().split())
            reference_words = set(reference.lower().split())
            overlap = len(response_words & reference_words) / max(len(reference_words), 1)
            score = 0.4 + (overlap * 0.6)

        return max(0.0, min(1.0, score))

    def score_response(
        self,
        response: str,
        question: str = "",
        reference: str = None
    ) -> Dict[str, float]:
        """
        Complete scoring of a response

        Returns:
            Dict with individual scores and overall score
        """
        clarity = self.score_clarity(response)
        depth = self.score_depth(response, question)
        formatting = self.score_formatting(response)
        correctness = self.score_correctness(response, question, reference)

        # Calculate weighted overall score
        overall = (
            clarity * self.weights['clarity'] +
            depth * self.weights['depth'] +
            formatting * self.weights['formatting'] +
            correctness * self.weights['correctness']
        )

        return {
            'clarity_score': round(clarity, 3),
            'depth_score': round(depth, 3),
            'formatting_score': round(formatting, 3),
            'correctness_score': round(correctness, 3),
            'overall_score': round(overall, 3)
        }

    def compare_responses(self, responses: Dict[str, str], question: str = "") -> Dict[str, Dict]:
        """
        Score and compare multiple responses

        Args:
            responses: Dict mapping llm_name to response_text
            question: The question being answered

        Returns:
            Dict with scores for each LLM and ranking
        """
        results = {}

        for llm_name, response_text in responses.items():
            scores = self.score_response(response_text, question)
            results[llm_name] = scores

        # Rank by overall score
        ranked = sorted(
            results.items(),
            key=lambda x: x[1]['overall_score'],
            reverse=True
        )

        return {
            'scores': results,
            'ranking': [llm_name for llm_name, _ in ranked],
            'best': ranked[0][0] if ranked else None
        }
