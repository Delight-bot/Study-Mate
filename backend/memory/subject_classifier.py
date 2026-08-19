"""
Subject Classifier - Determines the subject area of a question
Part of Feature #3: Memory-Based Subject Profiling
"""

from typing import Dict, List, Tuple
import re

class SubjectClassifier:
    """Classifies questions into subject areas"""

    def __init__(self):
        # Define keywords for each subject
        self.subject_keywords = {
            'Chemistry': [
                'molecule', 'atom', 'chemical', 'reaction', 'compound', 'element',
                'periodic', 'bond', 'electron', 'proton', 'neutron', 'acid', 'base',
                'pH', 'solution', 'catalyst', 'oxidation', 'reduction', 'molar',
                'stoichiometry', 'organic', 'inorganic', 'valence'
            ],
            'Calculus': [
                'derivative', 'integral', 'limit', 'function', 'differential',
                'continuous', 'convergent', 'divergent', 'series', 'sequence',
                'tangent', 'slope', 'rate', 'area', 'volume', 'optimization',
                'maxima', 'minima', 'critical point', 'chain rule', 'dx', 'dy'
            ],
            'Programming': [
                'code', 'function', 'variable', 'loop', 'array', 'string', 'class',
                'object', 'algorithm', 'data structure', 'compile', 'debug', 'syntax',
                'python', 'javascript', 'java', 'c++', 'api', 'database', 'framework',
                'library', 'method', 'recursion', 'iteration', 'boolean', 'integer'
            ],
            'Physics': [
                'force', 'motion', 'energy', 'mass', 'velocity', 'acceleration',
                'momentum', 'friction', 'gravity', 'wave', 'frequency', 'amplitude',
                'quantum', 'particle', 'field', 'electric', 'magnetic', 'current',
                'voltage', 'circuit', 'thermodynamics', 'entropy', 'work', 'power'
            ],
            'Biology': [
                'cell', 'dna', 'rna', 'protein', 'gene', 'chromosome', 'organism',
                'species', 'evolution', 'natural selection', 'enzyme', 'membrane',
                'mitochondria', 'chloroplast', 'photosynthesis', 'respiration',
                'bacteria', 'virus', 'tissue', 'organ', 'system', 'ecosystem'
            ],
            'History': [
                'war', 'revolution', 'empire', 'dynasty', 'century', 'ancient',
                'medieval', 'modern', 'civilization', 'kingdom', 'treaty', 'battle',
                'historical', 'period', 'era', 'colonization', 'independence',
                'democracy', 'monarchy', 'president', 'king', 'queen'
            ],
            'Literature': [
                'novel', 'poem', 'author', 'character', 'plot', 'theme', 'metaphor',
                'symbolism', 'narrative', 'prose', 'verse', 'stanza', 'chapter',
                'protagonist', 'antagonist', 'literary', 'shakespeare', 'poetry',
                'fiction', 'non-fiction', 'genre', 'writing', 'book'
            ]
        }

        # Compile regex patterns for better matching
        self.subject_patterns = {}
        for subject, keywords in self.subject_keywords.items():
            pattern = r'\b(' + '|'.join(re.escape(kw) for kw in keywords) + r')\b'
            self.subject_patterns[subject] = re.compile(pattern, re.IGNORECASE)

    def classify(self, question: str) -> Tuple[str, float, Dict[str, int]]:
        """
        Classify a question into a subject area

        Args:
            question: The question text

        Returns:
            Tuple of (subject_name, confidence, match_counts)
        """
        # Count keyword matches for each subject
        match_counts = {}

        for subject, pattern in self.subject_patterns.items():
            matches = pattern.findall(question)
            match_counts[subject] = len(matches)

        # Find the subject with the most matches
        if not any(match_counts.values()):
            # No matches found, default to 'General'
            return 'General', 0.3, match_counts

        max_matches = max(match_counts.values())
        best_subject = max(match_counts, key=match_counts.get)

        # Calculate confidence
        total_matches = sum(match_counts.values())
        confidence = match_counts[best_subject] / total_matches if total_matches > 0 else 0

        # Boost confidence if there are multiple matches for the same subject
        if max_matches > 1:
            confidence = min(1.0, confidence + 0.2)

        # If confidence is too low, classify as 'General'
        if confidence < 0.4:
            return 'General', confidence, match_counts

        return best_subject, round(confidence, 3), match_counts

    def classify_with_context(
        self,
        question: str,
        user_history: List[Dict] = None
    ) -> Tuple[str, float]:
        """
        Classify with additional context from user history

        Args:
            question: The question text
            user_history: List of previous questions and their subjects

        Returns:
            Tuple of (subject_name, confidence)
        """
        # Get base classification
        subject, confidence, match_counts = self.classify(question)

        # If we have user history, boost confidence for subjects the user asks about often
        if user_history and len(user_history) > 0:
            # Count subject frequency in history
            subject_freq = {}
            for item in user_history:
                prev_subject = item.get('subject', 'General')
                subject_freq[prev_subject] = subject_freq.get(prev_subject, 0) + 1

            # If the classified subject appears frequently in history, boost confidence
            if subject in subject_freq:
                frequency_bonus = min(0.2, subject_freq[subject] / len(user_history))
                confidence = min(1.0, confidence + frequency_bonus)

        return subject, round(confidence, 3)

    def get_related_subjects(self, subject: str) -> List[str]:
        """Get subjects that are related to the given subject"""
        related = {
            'Chemistry': ['Biology', 'Physics'],
            'Physics': ['Calculus', 'Chemistry'],
            'Calculus': ['Physics', 'Programming'],
            'Programming': ['Calculus', 'General'],
            'Biology': ['Chemistry', 'General'],
            'History': ['Literature', 'General'],
            'Literature': ['History', 'General'],
            'General': []
        }

        return related.get(subject, [])

    def suggest_subject(self, question: str) -> List[Tuple[str, float]]:
        """
        Suggest possible subjects with confidence scores

        Returns:
            List of (subject, confidence) tuples, sorted by confidence
        """
        subject, confidence, match_counts = self.classify(question)

        # Create suggestions based on match counts
        suggestions = []

        for subj, count in match_counts.items():
            if count > 0:
                total = sum(match_counts.values())
                conf = count / total if total > 0 else 0
                suggestions.append((subj, round(conf, 3)))

        # Add the main classification if not already in list
        if not any(s[0] == subject for s in suggestions):
            suggestions.append((subject, confidence))

        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions[:3]  # Return top 3 suggestions
