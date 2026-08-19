"""
Routing Engine - Decides which LLM to prioritize based on user profiles
Part of Feature #3: Memory-Based Subject Profiling (YOUR FAVORITE!)
"""

from typing import Dict, List, Optional, Tuple
from models import SubjectProfile

class RoutingEngine:
    """
    Intelligently routes questions to the best LLM based on:
    - User's subject-specific profiles
    - Historical performance
    - Question difficulty
    - Confidence levels
    """

    def __init__(self):
        self.confidence_threshold_high = 0.7
        self.confidence_threshold_medium = 0.5

        # Default LLM strengths (used when no profile exists)
        self.default_strengths = {
            'gpt': ['general', 'explanation', 'creative'],
            'claude': ['reasoning', 'analysis', 'detailed'],
            'gemini': ['creative', 'visual', 'examples'],
            'deepseek': ['technical', 'code', 'mathematical'],
            'llama': ['practical', 'straightforward', 'efficient']
        }

    def route(
        self,
        question: str,
        subject: str,
        profile: Optional[SubjectProfile] = None,
        difficulty: str = 'medium'
    ) -> Dict[str, any]:
        """
        Main routing method - decides which LLM(s) to prioritize

        Args:
            question: The question being asked
            subject: Subject classification
            profile: User's profile for this subject (if available)
            difficulty: Question difficulty level

        Returns:
            Dict with routing decision and reasoning
        """
        if profile and profile.total_questions >= 3:
            # Use profile-based routing
            return self._route_with_profile(question, subject, profile, difficulty)
        else:
            # Use default routing
            return self._route_default(question, subject, difficulty)

    def _route_with_profile(
        self,
        question: str,
        subject: str,
        profile: SubjectProfile,
        difficulty: str
    ) -> Dict[str, any]:
        """
        Route based on user's established profile

        This is the CORE of Feature #3!
        """
        routing = {
            'strategy': 'profile_based',
            'subject': subject,
            'primary_llm': profile.best_llm,
            'confidence': profile.confidence,
            'reasoning': []
        }

        # High confidence - strongly recommend the best LLM
        if profile.confidence >= self.confidence_threshold_high:
            routing['priority_order'] = self._get_priority_order_high_confidence(profile)
            routing['reasoning'].append(
                f"Strong historical preference for {profile.best_llm.upper()} "
                f"in {subject} ({profile.total_questions} interactions, "
                f"{profile.confidence:.0%} confidence)"
            )
            routing['recommendation'] = f"Strongly recommend starting with {profile.best_llm.upper()}"

        # Medium confidence - suggest best but keep options open
        elif profile.confidence >= self.confidence_threshold_medium:
            routing['priority_order'] = self._get_priority_order_medium_confidence(profile)
            routing['reasoning'].append(
                f"{profile.best_llm.upper()} has performed well for you in {subject}, "
                f"but also consider alternatives"
            )
            routing['recommendation'] = f"Recommend {profile.best_llm.upper()}, but review other options"

        # Low confidence - balanced approach
        else:
            routing['priority_order'] = self._get_priority_order_low_confidence(profile)
            routing['reasoning'].append(
                f"Still building your profile for {subject}. "
                f"Currently leaning toward {profile.best_llm.upper()}"
            )
            routing['recommendation'] = "Review all options to help build your profile"

        # Adjust for difficulty
        if difficulty == 'hard':
            routing['reasoning'].append(
                "This is a challenging question. Consider reviewing multiple responses."
            )

        return routing

    def _route_default(
        self,
        question: str,
        subject: str,
        difficulty: str
    ) -> Dict[str, any]:
        """
        Default routing when no profile exists

        Uses subject-based heuristics
        """
        # Subject-specific defaults
        subject_defaults = {
            'Chemistry': 'claude',      # Good at scientific reasoning
            'Calculus': 'gpt',          # Strong at math
            'Programming': 'deepseek',   # Specialized in code
            'Physics': 'claude',         # Good at complex reasoning
            'Biology': 'gpt',            # Good at explanations
            'History': 'claude',         # Good at detailed analysis
            'Literature': 'claude',      # Strong at analysis
            'General': 'gpt'             # Good all-rounder
        }

        primary_llm = subject_defaults.get(subject, 'gpt')

        routing = {
            'strategy': 'default',
            'subject': subject,
            'primary_llm': primary_llm,
            'confidence': 0.5,
            'priority_order': [primary_llm, 'gpt', 'claude', 'gemini', 'deepseek', 'llama'],
            'reasoning': [
                f"No profile data for {subject} yet",
                f"Using {primary_llm.upper()} as default for {subject}",
                "Try answering a few questions to build your personalized profile!"
            ],
            'recommendation': "Review all responses to help us learn your preferences"
        }

        # Remove duplicate from priority order
        routing['priority_order'] = list(dict.fromkeys(routing['priority_order']))

        return routing

    def _get_priority_order_high_confidence(self, profile: SubjectProfile) -> List[str]:
        """Get priority order when confidence is high"""
        wins = {
            'gpt': profile.wins_gpt,
            'claude': profile.wins_claude,
            'gemini': profile.wins_gemini,
            'deepseek': profile.wins_deepseek,
            'llama': profile.wins_llama
        }

        # Sort by wins
        sorted_llms = sorted(wins.items(), key=lambda x: x[1], reverse=True)

        # Return best first, then others in order
        return [llm for llm, _ in sorted_llms]

    def _get_priority_order_medium_confidence(self, profile: SubjectProfile) -> List[str]:
        """Get priority order when confidence is medium"""
        wins = {
            'gpt': profile.wins_gpt,
            'claude': profile.wins_claude,
            'gemini': profile.wins_gemini,
            'deepseek': profile.wins_deepseek,
            'llama': profile.wins_llama
        }

        # Sort by wins
        sorted_llms = sorted(wins.items(), key=lambda x: x[1], reverse=True)

        # Return top 3 first, then others
        top_three = [llm for llm, _ in sorted_llms[:3]]
        others = [llm for llm, _ in sorted_llms[3:]]

        return top_three + others

    def _get_priority_order_low_confidence(self, profile: SubjectProfile) -> List[str]:
        """Get priority order when confidence is low - more balanced"""
        # Still show best first, but indicate uncertainty
        return [profile.best_llm, 'gpt', 'claude', 'gemini', 'deepseek', 'llama']

    def should_auto_select(self, profile: SubjectProfile) -> bool:
        """
        Determine if we should auto-select the best LLM
        (only when confidence is very high)

        Returns:
            True if confidence is high enough for auto-selection
        """
        return (
            profile is not None and
            profile.confidence >= 0.85 and
            profile.total_questions >= 10
        )

    def get_routing_suggestions(
        self,
        profiles: Dict[str, SubjectProfile]
    ) -> Dict[str, any]:
        """
        Get overall routing suggestions across all subjects

        Args:
            profiles: Dict mapping subject name to SubjectProfile

        Returns:
            Summary of routing recommendations
        """
        if not profiles:
            return {
                'overall_status': 'new_user',
                'message': 'No profiles yet. Start asking questions to build your personalized routing!',
                'recommendations': []
            }

        # Analyze profile quality
        strong_profiles = []
        developing_profiles = []
        weak_profiles = []

        for subject, profile in profiles.items():
            if profile.confidence >= 0.7 and profile.total_questions >= 10:
                strong_profiles.append(subject)
            elif profile.confidence >= 0.5 or profile.total_questions >= 5:
                developing_profiles.append(subject)
            else:
                weak_profiles.append(subject)

        # Generate recommendations
        recommendations = []

        if strong_profiles:
            recommendations.append(
                f"✅ Strong profiles for: {', '.join(strong_profiles)}. "
                "We'll automatically prioritize your preferred LLMs for these subjects."
            )

        if developing_profiles:
            recommendations.append(
                f"🔄 Building profiles for: {', '.join(developing_profiles)}. "
                "Keep using the system to improve recommendations."
            )

        if weak_profiles:
            recommendations.append(
                f"📝 New subjects: {', '.join(weak_profiles)}. "
                "Ask more questions in these areas to build your profile."
            )

        # Overall best LLM
        total_wins = {
            'gpt': sum(p.wins_gpt for p in profiles.values()),
            'claude': sum(p.wins_claude for p in profiles.values()),
            'gemini': sum(p.wins_gemini for p in profiles.values()),
            'deepseek': sum(p.wins_deepseek for p in profiles.values()),
            'llama': sum(p.wins_llama for p in profiles.values())
        }

        overall_best = max(total_wins, key=total_wins.get) if any(total_wins.values()) else 'gpt'

        return {
            'overall_status': 'active_user',
            'overall_best_llm': overall_best,
            'strong_profiles': len(strong_profiles),
            'developing_profiles': len(developing_profiles),
            'weak_profiles': len(weak_profiles),
            'recommendations': recommendations,
            'total_interactions': sum(p.total_questions for p in profiles.values())
        }

    def explain_routing_decision(
        self,
        routing_result: Dict[str, any]
    ) -> str:
        """
        Generate a human-readable explanation of the routing decision

        Returns:
            Explanation string
        """
        strategy = routing_result.get('strategy', 'unknown')
        primary = routing_result.get('primary_llm', 'gpt').upper()
        confidence = routing_result.get('confidence', 0)

        if strategy == 'profile_based':
            if confidence >= self.confidence_threshold_high:
                return (
                    f"Based on your history, {primary} consistently provides the best "
                    f"answers for you in this subject. I'm showing it first."
                )
            elif confidence >= self.confidence_threshold_medium:
                return (
                    f"You tend to prefer {primary} for this subject, but it's worth "
                    "reviewing other options too."
                )
            else:
                return (
                    f"Still learning your preferences. {primary} is currently leading, "
                    "but we need more data."
                )
        else:
            return (
                f"This is your first time with this subject. I'm suggesting {primary} "
                "as a starting point based on general strengths."
            )
