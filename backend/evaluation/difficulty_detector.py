"""
Feature #3: Difficulty Detection
Analyzes questions to determine their complexity level
"""

import re
from typing import Dict, Tuple

class DifficultyDetector:
    """Detects the difficulty level of questions"""

    def __init__(self):
        # Keywords that indicate different difficulty levels
        self.easy_keywords = [
            'what is', 'define', 'list', 'name', 'who', 'when', 'where',
            'simple', 'basic', 'introduction'
        ]

        self.medium_keywords = [
            'how', 'why', 'explain', 'describe', 'compare', 'difference',
            'analyze', 'calculate', 'solve'
        ]

        self.hard_keywords = [
            'prove', 'derive', 'optimize', 'design', 'implement', 'evaluate',
            'critique', 'synthesize', 'justify', 'formulate', 'deduce'
        ]

        # Technical complexity indicators
        self.technical_indicators = [
            'algorithm', 'theorem', 'equation', 'formula', 'proof',
            'integration', 'derivative', 'molecular', 'quantum', 'recursive'
        ]

    def count_keyword_matches(self, question: str, keywords: list) -> int:
        """Count how many keywords from a list appear in the question"""
        question_lower = question.lower()
        return sum(1 for keyword in keywords if keyword in question_lower)

    def analyze_complexity(self, question: str) -> Dict[str, float]:
        """
        Analyze various complexity factors

        Returns:
            Dict with complexity metrics
        """
        # Word count
        words = question.split()
        word_count = len(words)

        # Average word length
        avg_word_length = sum(len(word) for word in words) / max(len(words), 1)

        # Technical term density
        technical_count = self.count_keyword_matches(question, self.technical_indicators)
        technical_density = technical_count / max(len(words), 1)

        # Sentence structure complexity
        clauses = len(re.findall(r'[,;]', question))
        nested_complexity = clauses / max(len(words), 1)

        # Mathematical expressions
        has_math = bool(re.search(r'[\d+\-*/^=∫∑∏√]', question))
        math_symbols = len(re.findall(r'[∫∑∏√∂∇α-ωΑ-Ω]', question))

        # Multiple parts/sub-questions
        parts = len(re.findall(r'\b(?:part\s+[a-z]|\d+\)|\([a-z]\))\b', question, re.I))

        return {
            'word_count': word_count,
            'avg_word_length': avg_word_length,
            'technical_density': technical_density,
            'nested_complexity': nested_complexity,
            'has_math': has_math,
            'math_symbols': math_symbols,
            'parts': parts
        }

    def calculate_difficulty_score(self, question: str) -> float:
        """
        Calculate a difficulty score from 0.0 (easy) to 1.0 (hard)
        """
        # Count keyword matches for each difficulty level
        easy_count = self.count_keyword_matches(question, self.easy_keywords)
        medium_count = self.count_keyword_matches(question, self.medium_keywords)
        hard_count = self.count_keyword_matches(question, self.hard_keywords)

        # Get complexity metrics
        complexity = self.analyze_complexity(question)

        # Base score from keyword analysis
        if hard_count > 0:
            base_score = 0.7 + (hard_count * 0.1)
        elif medium_count > 0:
            base_score = 0.4 + (medium_count * 0.1)
        elif easy_count > 0:
            base_score = 0.2
        else:
            base_score = 0.5  # Default

        # Adjust based on complexity factors
        score_adjustments = 0

        # Word count (longer questions often more complex)
        if complexity['word_count'] > 50:
            score_adjustments += 0.15
        elif complexity['word_count'] > 30:
            score_adjustments += 0.1

        # Technical density
        score_adjustments += complexity['technical_density'] * 0.2

        # Nested complexity
        score_adjustments += complexity['nested_complexity'] * 0.1

        # Math presence
        if complexity['has_math']:
            score_adjustments += 0.1
            score_adjustments += complexity['math_symbols'] * 0.05

        # Multiple parts
        if complexity['parts'] > 0:
            score_adjustments += complexity['parts'] * 0.1

        final_score = base_score + score_adjustments

        # Clamp between 0 and 1
        return max(0.0, min(1.0, final_score))

    def classify_difficulty(self, question: str) -> Tuple[str, float, Dict]:
        """
        Classify question difficulty and return detailed analysis

        Returns:
            Tuple of (difficulty_level, score, complexity_metrics)
            where difficulty_level is 'easy', 'medium', or 'hard'
        """
        score = self.calculate_difficulty_score(question)
        complexity = self.analyze_complexity(question)

        # Classify based on score
        if score < 0.35:
            level = 'easy'
        elif score < 0.65:
            level = 'medium'
        else:
            level = 'hard'

        return level, round(score, 3), complexity

    def estimate_response_time(self, difficulty_score: float) -> float:
        """
        Estimate how long an LLM might take to respond

        Returns:
            Estimated time in seconds
        """
        # More difficult questions typically take longer
        base_time = 2.0  # seconds
        additional_time = difficulty_score * 5.0  # up to 5 more seconds

        return base_time + additional_time

    def recommend_approach(self, question: str) -> Dict[str, any]:
        """
        Recommend how to approach answering this question

        Returns:
            Dict with recommendations
        """
        level, score, complexity = self.classify_difficulty(question)

        recommendations = {
            'difficulty': level,
            'score': score,
            'estimated_time': self.estimate_response_time(score),
            'approach': []
        }

        # Add specific recommendations based on difficulty
        if level == 'easy':
            recommendations['approach'].append("Provide clear, concise answer")
            recommendations['approach'].append("Include basic examples if relevant")
        elif level == 'medium':
            recommendations['approach'].append("Provide detailed explanation")
            recommendations['approach'].append("Break down concepts step-by-step")
            recommendations['approach'].append("Include examples and comparisons")
        else:  # hard
            recommendations['approach'].append("Provide comprehensive analysis")
            recommendations['approach'].append("Include technical details and proofs")
            recommendations['approach'].append("Address edge cases and assumptions")
            recommendations['approach'].append("Provide multiple examples")

        # Add specific recommendations based on complexity
        if complexity['has_math']:
            recommendations['approach'].append("Show mathematical workings clearly")

        if complexity['parts'] > 0:
            recommendations['approach'].append("Address each part separately")

        if complexity['technical_density'] > 0.05:
            recommendations['approach'].append("Define technical terms")

        return recommendations
