from typing import Dict, Optional
from models import UserPreference, SubjectProfile

class PromptOptimizer:
    """
    Feature #1: Adaptive Prompt Rewriting
    Customizes prompts based on user preferences, subject, and difficulty level
    """

    def __init__(self):
        self.llm_specific_templates = {
            "gpt": {
                "prefix": "Please provide a clear and structured response.",
                "suffix": ""
            },
            "claude": {
                "prefix": "Let me help you with that.",
                "suffix": "Please provide a thorough explanation with careful reasoning."
            },
            "gemini": {
                "prefix": "",
                "suffix": "Include relevant examples where appropriate."
            },
            "deepseek": {
                "prefix": "Analyzing your question:",
                "suffix": "Provide technical accuracy and depth."
            },
            "llama": {
                "prefix": "Here's my response:",
                "suffix": "Focus on practical application."
            }
        }

    def optimize_prompt(
        self,
        question: str,
        llm_name: str,
        user_preference: Optional[UserPreference] = None,
        subject: Optional[str] = None,
        difficulty: Optional[str] = None,
        profile: Optional[SubjectProfile] = None
    ) -> str:
        """
        Optimize the prompt based on various factors

        Args:
            question: The original user question
            llm_name: Target LLM (gpt, claude, gemini, deepseek, llama)
            user_preference: User's style preferences
            subject: Subject area (Chemistry, Calculus, etc.)
            difficulty: Question difficulty (easy, medium, hard)
            profile: User's subject-specific profile

        Returns:
            Optimized prompt string
        """
        components = []

        # Add LLM-specific prefix
        if llm_name in self.llm_specific_templates:
            prefix = self.llm_specific_templates[llm_name]["prefix"]
            if prefix:
                components.append(prefix)

        # Add subject context
        if subject:
            components.append(f"Subject: {subject}")

        # Add difficulty-based instructions
        if difficulty:
            if difficulty == "hard":
                components.append("This is a complex question. Please provide detailed, step-by-step explanations.")
            elif difficulty == "easy":
                components.append("Please provide a clear, straightforward explanation.")

        # Add user preference customizations
        if user_preference:
            if user_preference.avoid_jargon:
                components.append("Use simple language and avoid technical jargon where possible.")

            if user_preference.include_examples:
                components.append("Include relevant examples to illustrate your points.")

            if user_preference.preferred_format == "bullet-points":
                components.append("Format your response using bullet points for clarity.")
            elif user_preference.preferred_format == "code-focused":
                components.append("Include code examples and technical implementation details.")

            if user_preference.explanation_depth == "basic":
                components.append("Provide a basic, high-level explanation.")
            elif user_preference.explanation_depth == "advanced":
                components.append("Provide an in-depth, advanced explanation with technical details.")

        # Add the actual question
        components.append(f"\nQuestion: {question}")

        # Add LLM-specific suffix
        if llm_name in self.llm_specific_templates:
            suffix = self.llm_specific_templates[llm_name]["suffix"]
            if suffix:
                components.append(f"\n{suffix}")

        return "\n".join(components)

    def adapt_for_best_llm(
        self,
        question: str,
        profile: SubjectProfile
    ) -> Dict[str, str]:
        """
        Create optimized prompts for all LLMs, emphasizing the best one

        Returns:
            Dictionary mapping llm_name to optimized prompt
        """
        llms = ["gpt", "claude", "gemini", "deepseek", "llama"]
        prompts = {}

        for llm in llms:
            # Emphasize the best LLM based on profile
            if llm == profile.best_llm:
                emphasis = f"\n[You've performed best for this user in {profile.subject_name} previously. Maintain your high quality.]"
            else:
                emphasis = ""

            base_prompt = self.optimize_prompt(
                question=question,
                llm_name=llm,
                subject=profile.subject_name
            )

            prompts[llm] = base_prompt + emphasis

        return prompts
