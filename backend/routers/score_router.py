from fastapi import APIRouter, HTTPException
from models import UserChoice, UserFeedback
from database import execute_query, execute_update
import json

router = APIRouter()

@router.post("/choose")
async def record_user_choice(choice: UserChoice):
    """
    Record which LLM the user chose as the best response

    This updates:
    1. user_choices table
    2. profiles table (win counts and best_llm)
    """
    try:
        # Get subject ID
        subject_id = None
        if choice.subject_id:
            subject_id = choice.subject_id
        else:
            # Try to infer from the question
            result = await execute_query(
                """SELECT subject_id FROM llm_responses
                   WHERE user_id = ? AND question = ?
                   LIMIT 1""",
                (choice.user_id, choice.question)
            )
            if result:
                subject_id = result[0]['subject_id']

        # Record the choice
        await execute_update(
            """INSERT INTO user_choices
               (user_id, question, subject_id, chosen_llm, all_responses, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                choice.user_id,
                choice.question,
                subject_id,
                choice.chosen_llm,
                json.dumps(choice.all_response_ids),
                json.dumps(choice.metadata) if choice.metadata else None
            )
        )

        # Update profile wins
        if subject_id:
            # Check if profile exists
            profile = await execute_query(
                "SELECT * FROM profiles WHERE user_id = ? AND subject_id = ?",
                (choice.user_id, subject_id)
            )

            if profile:
                # Update existing profile
                column_name = f"wins_{choice.chosen_llm}"
                await execute_update(
                    f"""UPDATE profiles
                       SET {column_name} = {column_name} + 1,
                           total_questions = total_questions + 1,
                           last_updated = CURRENT_TIMESTAMP
                       WHERE user_id = ? AND subject_id = ?""",
                    (choice.user_id, subject_id)
                )

                # Recalculate best LLM
                updated_profile = await execute_query(
                    "SELECT * FROM profiles WHERE user_id = ? AND subject_id = ?",
                    (choice.user_id, subject_id)
                )
                if updated_profile:
                    profile_dict = dict(updated_profile[0])
                    best_llm = max(
                        ['gpt', 'claude', 'gemini', 'deepseek', 'llama'],
                        key=lambda x: profile_dict.get(f'wins_{x}', 0)
                    )
                    total = profile_dict['total_questions']
                    confidence = profile_dict.get(f'wins_{best_llm}', 0) / total if total > 0 else 0

                    await execute_update(
                        """UPDATE profiles
                           SET best_llm = ?, confidence = ?
                           WHERE user_id = ? AND subject_id = ?""",
                        (best_llm, confidence, choice.user_id, subject_id)
                    )
            else:
                # Create new profile
                await execute_update(
                    f"""INSERT INTO profiles
                       (user_id, subject_id, best_llm, confidence, wins_{choice.chosen_llm}, total_questions)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (choice.user_id, subject_id, choice.chosen_llm, 1.0, 1, 1)
                )

        return {
            "success": True,
            "message": "Choice recorded successfully",
            "chosen_llm": choice.chosen_llm,
            "subject_id": subject_id
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording choice: {str(e)}")

@router.post("/feedback")
async def record_feedback(feedback: UserFeedback):
    """Record detailed user feedback on a specific response"""
    try:
        # Store feedback as metadata in a separate table or update the response
        # For now, we'll create a simple feedback log
        await execute_update(
            """INSERT INTO user_choices
               (user_id, question, chosen_llm, metadata)
               SELECT user_id, question, llm_name, ?
               FROM llm_responses
               WHERE id = ?""",
            (
                json.dumps({
                    "rating": feedback.rating,
                    "comments": feedback.comments,
                    "helpful": feedback.helpful,
                    "needs_improvement": feedback.needs_improvement
                }),
                feedback.response_id
            )
        )

        return {"success": True, "message": "Feedback recorded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: int):
    """Get overall statistics for a user"""
    try:
        # Get total questions asked
        total_questions = await execute_query(
            "SELECT COUNT(DISTINCT question) as count FROM llm_responses WHERE user_id = ?",
            (user_id,)
        )

        # Get choice breakdown
        choices = await execute_query(
            """SELECT chosen_llm, COUNT(*) as count
               FROM user_choices
               WHERE user_id = ?
               GROUP BY chosen_llm""",
            (user_id,)
        )

        return {
            "user_id": user_id,
            "total_questions": total_questions[0]['count'] if total_questions else 0,
            "choice_breakdown": {row['chosen_llm']: row['count'] for row in choices}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
