from fastapi import APIRouter, Depends, HTTPException
from typing import List
from auth import get_current_user
from models import SubjectProfile, ProfileSummary
from database import execute_query

router = APIRouter()

@router.get("/me", response_model=ProfileSummary)
async def get_user_profile(current_user: dict = Depends(get_current_user)):
    """
    Get complete profile for the current user across all subjects

    Feature #3: Memory-Based Subject Profiling
    Returns which LLM performs best for each subject
    """
    user_id = current_user["user_id"]
    try:
        # Get all profiles for this user
        results = await execute_query(
            """SELECT p.*, s.name as subject_name
               FROM profiles p
               JOIN subjects s ON p.subject_id = s.id
               WHERE p.user_id = ?
               ORDER BY p.total_questions DESC""",
            (user_id,)
        )

        profiles = []
        for row in results:
            profile = SubjectProfile(
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
            profiles.append(profile)

        # Calculate overall best LLM
        total_wins = {
            'gpt': sum(p.wins_gpt for p in profiles),
            'claude': sum(p.wins_claude for p in profiles),
            'gemini': sum(p.wins_gemini for p in profiles),
            'deepseek': sum(p.wins_deepseek for p in profiles),
            'llama': sum(p.wins_llama for p in profiles)
        }

        overall_best = max(total_wins, key=total_wins.get) if any(total_wins.values()) else "gpt"
        total_interactions = sum(p.total_questions for p in profiles)

        return ProfileSummary(
            user_id=user_id,
            profiles=profiles,
            overall_best_llm=overall_best,
            total_interactions=total_interactions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching profile: {str(e)}")

@router.get("/me/subject/{subject_name}")
async def get_subject_profile(subject_name: str, current_user: dict = Depends(get_current_user)):
    """Get the current user's profile for a specific subject"""
    user_id = current_user["user_id"]
    try:
        # Get subject ID
        subject = await execute_query(
            "SELECT id FROM subjects WHERE name = ?",
            (subject_name,)
        )

        if not subject:
            raise HTTPException(status_code=404, detail="Subject not found")

        subject_id = subject[0]['id']

        # Get profile
        result = await execute_query(
            """SELECT p.*, s.name as subject_name
               FROM profiles p
               JOIN subjects s ON p.subject_id = s.id
               WHERE p.user_id = ? AND p.subject_id = ?""",
            (user_id, subject_id)
        )

        if not result:
            return {
                "message": "No profile found for this subject yet",
                "user_id": user_id,
                "subject": subject_name
            }

        row = result[0]
        profile = SubjectProfile(
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

        return profile

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching subject profile: {str(e)}")

@router.get("/me/recommendations")
async def get_recommendations(subject: str = None, current_user: dict = Depends(get_current_user)):
    """
    Get LLM recommendations based on the current user's profile

    Returns which LLM to use for different subjects
    """
    user_id = current_user["user_id"]
    try:
        if subject:
            # Get recommendation for specific subject
            subject_result = await execute_query(
                "SELECT id FROM subjects WHERE name = ?",
                (subject,)
            )

            if not subject_result:
                return {"recommendation": "gpt", "confidence": 0.0, "message": "Subject not found, using default"}

            profile = await execute_query(
                "SELECT * FROM profiles WHERE user_id = ? AND subject_id = ?",
                (user_id, subject_result[0]['id'])
            )

            if not profile:
                return {"recommendation": "gpt", "confidence": 0.0, "message": "No profile data, using default"}

            return {
                "subject": subject,
                "recommendation": profile[0]['best_llm'],
                "confidence": profile[0]['confidence'],
                "total_questions": profile[0]['total_questions']
            }
        else:
            # Get recommendations for all subjects
            profiles = await execute_query(
                """SELECT s.name, p.best_llm, p.confidence, p.total_questions
                   FROM profiles p
                   JOIN subjects s ON p.subject_id = s.id
                   WHERE p.user_id = ?""",
                (user_id,)
            )

            recommendations = {}
            for row in profiles:
                recommendations[row['name']] = {
                    "llm": row['best_llm'],
                    "confidence": row['confidence'],
                    "questions": row['total_questions']
                }

            return {"user_id": user_id, "recommendations": recommendations}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")
