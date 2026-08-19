"""
User History Manager - Stores and refines user behavior patterns
Part of Feature #3: Memory-Based Subject Profiling
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json

class UserHistoryManager:
    """Manages user interaction history and behavior patterns"""

    def __init__(self, db_connection=None):
        self.db = db_connection

    async def add_interaction(
        self,
        user_id: int,
        question: str,
        subject: str,
        chosen_llm: str,
        all_responses: Dict[str, str],
        metadata: Dict = None
    ) -> bool:
        """
        Record a user interaction

        Args:
            user_id: User ID
            question: The question asked
            subject: Classified subject
            chosen_llm: Which LLM the user selected
            all_responses: All LLM responses
            metadata: Additional metadata

        Returns:
            Success status
        """
        from database import execute_update, execute_query

        # Get subject ID
        subject_result = await execute_query(
            "SELECT id FROM subjects WHERE name = ?",
            (subject,)
        )

        subject_id = subject_result[0]['id'] if subject_result else None

        # Store in user_choices table
        await execute_update(
            """INSERT INTO user_choices
               (user_id, question, subject_id, chosen_llm, all_responses, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                question,
                subject_id,
                chosen_llm,
                json.dumps(list(all_responses.keys())),
                json.dumps(metadata) if metadata else None
            )
        )

        return True

    async def get_user_history(
        self,
        user_id: int,
        subject: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get user's interaction history

        Args:
            user_id: User ID
            subject: Optional subject filter
            limit: Maximum number of records

        Returns:
            List of interaction records
        """
        from database import execute_query

        if subject:
            # Get subject ID
            subject_result = await execute_query(
                "SELECT id FROM subjects WHERE name = ?",
                (subject,)
            )

            if not subject_result:
                return []

            subject_id = subject_result[0]['id']

            results = await execute_query(
                """SELECT uc.*, s.name as subject_name
                   FROM user_choices uc
                   LEFT JOIN subjects s ON uc.subject_id = s.id
                   WHERE uc.user_id = ? AND uc.subject_id = ?
                   ORDER BY uc.created_at DESC
                   LIMIT ?""",
                (user_id, subject_id, limit)
            )
        else:
            results = await execute_query(
                """SELECT uc.*, s.name as subject_name
                   FROM user_choices uc
                   LEFT JOIN subjects s ON uc.subject_id = s.id
                   WHERE uc.user_id = ?
                   ORDER BY uc.created_at DESC
                   LIMIT ?""",
                (user_id, limit)
            )

        return [dict(row) for row in results]

    async def get_preference_patterns(self, user_id: int) -> Dict[str, any]:
        """
        Analyze user's preference patterns

        Returns:
            Dict with pattern analysis
        """
        history = await self.get_user_history(user_id, limit=100)

        if not history:
            return {
                'total_interactions': 0,
                'favorite_llm': None,
                'subject_breakdown': {},
                'recent_trend': None
            }

        # Analyze LLM preferences
        llm_counts = {}
        subject_counts = {}

        for record in history:
            llm = record.get('chosen_llm')
            subject = record.get('subject_name', 'General')

            llm_counts[llm] = llm_counts.get(llm, 0) + 1
            subject_counts[subject] = subject_counts.get(subject, 0) + 1

        favorite_llm = max(llm_counts, key=llm_counts.get) if llm_counts else None

        # Analyze recent trend (last 10 interactions)
        recent = history[:10]
        recent_llm_counts = {}
        for record in recent:
            llm = record.get('chosen_llm')
            recent_llm_counts[llm] = recent_llm_counts.get(llm, 0) + 1

        recent_favorite = max(recent_llm_counts, key=recent_llm_counts.get) if recent_llm_counts else None

        return {
            'total_interactions': len(history),
            'favorite_llm': favorite_llm,
            'llm_breakdown': llm_counts,
            'subject_breakdown': subject_counts,
            'recent_trend': recent_favorite,
            'trend_shift': recent_favorite != favorite_llm if recent_favorite and favorite_llm else False
        }

    async def get_subject_specific_patterns(
        self,
        user_id: int,
        subject: str
    ) -> Dict[str, any]:
        """
        Get patterns for a specific subject

        Returns:
            Dict with subject-specific patterns
        """
        history = await self.get_user_history(user_id, subject=subject)

        if not history:
            return {
                'subject': subject,
                'interactions': 0,
                'preferred_llm': None,
                'consistency': 0.0
            }

        llm_counts = {}
        for record in history:
            llm = record.get('chosen_llm')
            llm_counts[llm] = llm_counts.get(llm, 0) + 1

        preferred_llm = max(llm_counts, key=llm_counts.get) if llm_counts else None

        # Calculate consistency (how often they choose the same LLM)
        if llm_counts and preferred_llm:
            consistency = llm_counts[preferred_llm] / len(history)
        else:
            consistency = 0.0

        return {
            'subject': subject,
            'interactions': len(history),
            'preferred_llm': preferred_llm,
            'llm_breakdown': llm_counts,
            'consistency': round(consistency, 3),
            'confidence': round(consistency, 3)  # Consistency maps to confidence
        }

    async def detect_behavior_changes(
        self,
        user_id: int,
        window_days: int = 30
    ) -> Dict[str, any]:
        """
        Detect if user's behavior has changed recently

        Returns:
            Dict with behavior change analysis
        """
        from database import execute_query

        # Get recent history
        cutoff_date = datetime.now() - timedelta(days=window_days)

        recent = await execute_query(
            """SELECT chosen_llm, subject_id, created_at
               FROM user_choices
               WHERE user_id = ? AND created_at >= ?
               ORDER BY created_at DESC""",
            (user_id, cutoff_date.isoformat())
        )

        # Get older history for comparison
        older = await execute_query(
            """SELECT chosen_llm, subject_id, created_at
               FROM user_choices
               WHERE user_id = ? AND created_at < ?
               ORDER BY created_at DESC
               LIMIT 50""",
            (user_id, cutoff_date.isoformat())
        )

        if not recent or not older:
            return {
                'has_changed': False,
                'confidence': 0.0,
                'details': 'Insufficient data'
            }

        # Compare LLM preferences
        recent_llms = {}
        for record in recent:
            llm = dict(record)['chosen_llm']
            recent_llms[llm] = recent_llms.get(llm, 0) + 1

        older_llms = {}
        for record in older:
            llm = dict(record)['chosen_llm']
            older_llms[llm] = older_llms.get(llm, 0) + 1

        # Normalize to percentages
        recent_total = len(recent)
        older_total = len(older)

        recent_pct = {llm: count / recent_total for llm, count in recent_llms.items()}
        older_pct = {llm: count / older_total for llm, count in older_llms.items()}

        # Calculate difference
        all_llms = set(recent_pct.keys()) | set(older_pct.keys())
        total_difference = sum(
            abs(recent_pct.get(llm, 0) - older_pct.get(llm, 0))
            for llm in all_llms
        )

        has_changed = total_difference > 0.3  # 30% threshold

        return {
            'has_changed': has_changed,
            'difference_score': round(total_difference, 3),
            'recent_preferences': recent_llms,
            'previous_preferences': older_llms,
            'window_days': window_days
        }

    def infer_user_style(self, history: List[Dict]) -> Dict[str, any]:
        """
        Infer user's preferred response style from their choices

        Returns:
            Dict with inferred style preferences
        """
        if not history:
            return {
                'style': 'unknown',
                'confidence': 0.0
            }

        # Analyze metadata if available
        styles = {
            'concise': 0,
            'detailed': 0,
            'example_heavy': 0,
            'technical': 0
        }

        for record in history:
            metadata = record.get('metadata')
            if metadata:
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        continue

                # Infer from feedback
                if 'preferred_format' in metadata:
                    format_pref = metadata['preferred_format']
                    if 'bullet' in format_pref:
                        styles['concise'] += 1
                    elif 'paragraph' in format_pref:
                        styles['detailed'] += 1

        # Determine dominant style
        if any(styles.values()):
            dominant_style = max(styles, key=styles.get)
            confidence = styles[dominant_style] / len(history)
        else:
            dominant_style = 'balanced'
            confidence = 0.5

        return {
            'style': dominant_style,
            'confidence': round(confidence, 3),
            'breakdown': styles
        }
