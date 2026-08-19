"""
Profile Builder - Builds and updates user subject performance profiles
Part of Feature #3: Memory-Based Subject Profiling (YOUR FAVORITE!)
"""

from typing import Dict, Optional
from models import SubjectProfile

class ProfileBuilder:
    """Builds and maintains user performance profiles per subject"""

    def __init__(self):
        self.min_interactions_for_confidence = 5  # Minimum interactions needed
        self.confidence_growth_rate = 0.1  # How fast confidence increases

    async def get_or_create_profile(
        self,
        user_id: int,
        subject: str
    ) -> SubjectProfile:
        """
        Get existing profile or create a new one

        Args:
            user_id: User ID
            subject: Subject name

        Returns:
            SubjectProfile object
        """
        from database import execute_query, execute_update

        # Get subject ID
        subject_result = await execute_query(
            "SELECT id FROM subjects WHERE name = ?",
            (subject,)
        )

        if not subject_result:
            # Create subject if it doesn't exist
            await execute_update(
                "INSERT INTO subjects (name) VALUES (?)",
                (subject,)
            )
            subject_result = await execute_query(
                "SELECT id FROM subjects WHERE name = ?",
                (subject,)
            )

        subject_id = subject_result[0]['id']

        # Check if profile exists
        profile_result = await execute_query(
            """SELECT p.*, s.name as subject_name
               FROM profiles p
               JOIN subjects s ON p.subject_id = s.id
               WHERE p.user_id = ? AND p.subject_id = ?""",
            (user_id, subject_id)
        )

        if profile_result:
            # Return existing profile
            row = dict(profile_result[0])
            return SubjectProfile(
                id=row['id'],
                user_id=row['user_id'],
                subject_id=row['subject_id'],
                subject_name=row['subject_name'],
                best_llm=row['best_llm'],
                confidence=row['confidence'],
                wins_gpt=row['wins_gpt'],
                wins_claude=row['wins_claude'],
                wins_gemini=row['wins_gemini'],
                wins_deepseek=row['wins_deepseek'],
                wins_llama=row['wins_llama'],
                total_questions=row['total_questions']
            )
        else:
            # Create new profile with defaults
            await execute_update(
                """INSERT INTO profiles
                   (user_id, subject_id, best_llm, confidence, total_questions)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, subject_id, 'gpt', 0.0, 0)
            )

            return SubjectProfile(
                user_id=user_id,
                subject_id=subject_id,
                subject_name=subject,
                best_llm='gpt',
                confidence=0.0,
                wins_gpt=0,
                wins_claude=0,
                wins_gemini=0,
                wins_deepseek=0,
                wins_llama=0,
                total_questions=0
            )

    async def update_profile(
        self,
        user_id: int,
        subject: str,
        chosen_llm: str
    ) -> SubjectProfile:
        """
        Update profile based on user's choice

        Args:
            user_id: User ID
            subject: Subject name
            chosen_llm: The LLM the user chose

        Returns:
            Updated SubjectProfile
        """
        from database import execute_update, execute_query

        # Get or create profile
        profile = await self.get_or_create_profile(user_id, subject)

        # Increment win count for chosen LLM
        win_column = f"wins_{chosen_llm}"

        await execute_update(
            f"""UPDATE profiles
               SET {win_column} = {win_column} + 1,
                   total_questions = total_questions + 1,
                   last_updated = CURRENT_TIMESTAMP
               WHERE user_id = ? AND subject_id = ?""",
            (user_id, profile.subject_id)
        )

        # Recalculate best LLM and confidence
        updated_data = await execute_query(
            """SELECT * FROM profiles
               WHERE user_id = ? AND subject_id = ?""",
            (user_id, profile.subject_id)
        )

        row = dict(updated_data[0])

        # Find best LLM
        llm_wins = {
            'gpt': row['wins_gpt'],
            'claude': row['wins_claude'],
            'gemini': row['wins_gemini'],
            'deepseek': row['wins_deepseek'],
            'llama': row['wins_llama']
        }

        best_llm = max(llm_wins, key=llm_wins.get)
        total_questions = row['total_questions']

        # Calculate confidence
        if total_questions < self.min_interactions_for_confidence:
            # Low confidence if not enough data
            confidence = 0.3 + (total_questions / self.min_interactions_for_confidence) * 0.3
        else:
            # Confidence based on win rate
            win_rate = llm_wins[best_llm] / total_questions
            confidence = min(0.95, 0.5 + win_rate * 0.5)  # Scale to 0.5-0.95

        # Update best_llm and confidence
        await execute_update(
            """UPDATE profiles
               SET best_llm = ?, confidence = ?
               WHERE user_id = ? AND subject_id = ?""",
            (best_llm, confidence, user_id, profile.subject_id)
        )

        # Return updated profile
        return SubjectProfile(
            id=row['id'],
            user_id=user_id,
            subject_id=profile.subject_id,
            subject_name=profile.subject_name,
            best_llm=best_llm,
            confidence=round(confidence, 3),
            wins_gpt=row['wins_gpt'],
            wins_claude=row['wins_claude'],
            wins_gemini=row['wins_gemini'],
            wins_deepseek=row['wins_deepseek'],
            wins_llama=row['wins_llama'],
            total_questions=total_questions
        )

    async def get_all_profiles(self, user_id: int) -> Dict[str, SubjectProfile]:
        """
        Get all subject profiles for a user

        Returns:
            Dict mapping subject name to SubjectProfile
        """
        from database import execute_query

        results = await execute_query(
            """SELECT p.*, s.name as subject_name
               FROM profiles p
               JOIN subjects s ON p.subject_id = s.id
               WHERE p.user_id = ?
               ORDER BY p.total_questions DESC""",
            (user_id,)
        )

        profiles = {}
        for row in results:
            row_dict = dict(row)
            profile = SubjectProfile(
                id=row_dict['id'],
                user_id=row_dict['user_id'],
                subject_id=row_dict['subject_id'],
                subject_name=row_dict['subject_name'],
                best_llm=row_dict['best_llm'],
                confidence=row_dict['confidence'],
                wins_gpt=row_dict['wins_gpt'],
                wins_claude=row_dict['wins_claude'],
                wins_gemini=row_dict['wins_gemini'],
                wins_deepseek=row_dict['wins_deepseek'],
                wins_llama=row_dict['wins_llama'],
                total_questions=row_dict['total_questions']
            )
            profiles[profile.subject_name] = profile

        return profiles

    def calculate_profile_strength(self, profile: SubjectProfile) -> str:
        """
        Determine how strong/reliable a profile is

        Returns:
            'weak', 'moderate', or 'strong'
        """
        if profile.total_questions < 3:
            return 'weak'
        elif profile.total_questions < 10:
            return 'moderate'
        else:
            return 'strong'

    async def get_profile_insights(
        self,
        user_id: int,
        subject: str
    ) -> Dict[str, any]:
        """
        Get detailed insights about a profile

        Returns:
            Dict with profile analysis and insights
        """
        profile = await self.get_or_create_profile(user_id, subject)

        if profile.total_questions == 0:
            return {
                'subject': subject,
                'status': 'no_data',
                'message': 'No interactions recorded yet for this subject',
                'recommendation': 'Try asking a few questions to build your profile'
            }

        # Calculate statistics
        llm_wins = {
            'gpt': profile.wins_gpt,
            'claude': profile.wins_claude,
            'gemini': profile.wins_gemini,
            'deepseek': profile.wins_deepseek,
            'llama': profile.wins_llama
        }

        # Win rates
        win_rates = {
            llm: (wins / profile.total_questions) if profile.total_questions > 0 else 0
            for llm, wins in llm_wins.items()
        }

        # Second best LLM
        sorted_llms = sorted(llm_wins.items(), key=lambda x: x[1], reverse=True)
        second_best = sorted_llms[1][0] if len(sorted_llms) > 1 else None

        # Diversity score (how spread out are the choices?)
        non_zero_llms = sum(1 for wins in llm_wins.values() if wins > 0)
        diversity = non_zero_llms / 5.0  # Out of 5 LLMs

        # Profile strength
        strength = self.calculate_profile_strength(profile)

        return {
            'subject': subject,
            'best_llm': profile.best_llm,
            'confidence': profile.confidence,
            'total_questions': profile.total_questions,
            'strength': strength,
            'win_rates': {k: round(v, 3) for k, v in win_rates.items()},
            'second_best': second_best,
            'diversity': round(diversity, 2),
            'insights': self._generate_insights(profile, win_rates, diversity, strength)
        }

    def _generate_insights(
        self,
        profile: SubjectProfile,
        win_rates: Dict[str, float],
        diversity: float,
        strength: str
    ) -> List[str]:
        """Generate human-readable insights"""
        insights = []

        # Confidence insights
        if profile.confidence > 0.8:
            insights.append(f"✅ Strong preference for {profile.best_llm.upper()} in {profile.subject_name}")
        elif profile.confidence > 0.6:
            insights.append(f"👍 {profile.best_llm.upper()} works well for you in {profile.subject_name}")
        else:
            insights.append(f"🤔 Still learning your preferences for {profile.subject_name}")

        # Data sufficiency
        if strength == 'weak':
            insights.append(f"📊 Limited data ({profile.total_questions} questions). Try a few more for better recommendations")
        elif strength == 'moderate':
            insights.append(f"📊 Building confidence ({profile.total_questions} questions)")
        else:
            insights.append(f"📊 Solid data foundation ({profile.total_questions} questions)")

        # Diversity insights
        if diversity > 0.8:
            insights.append("🌈 You've tried many different LLMs - good for finding the best fit!")
        elif diversity < 0.4:
            insights.append("💡 Consider trying other LLMs to find hidden gems")

        # Second place insights
        sorted_wins = sorted(
            [(llm, wins) for llm, wins in [
                ('gpt', profile.wins_gpt),
                ('claude', profile.wins_claude),
                ('gemini', profile.wins_gemini),
                ('deepseek', profile.wins_deepseek),
                ('llama', profile.wins_llama)
            ]],
            key=lambda x: x[1],
            reverse=True
        )

        if len(sorted_wins) > 1 and sorted_wins[1][1] > 0:
            second_best, second_wins = sorted_wins[1]
            if second_wins / profile.total_questions > 0.3:
                insights.append(f"⚡ {second_best.upper()} is also a strong choice ({second_wins} wins)")

        return insights
