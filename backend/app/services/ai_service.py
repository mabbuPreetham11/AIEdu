from collections.abc import Sequence

from app.core.config import settings
from app.schemas.assignment import AssignmentGenerateRequest


class AIService:
    def __init__(self) -> None:
        self.provider = settings.default_llm_provider

    def generate_notes(self, topics_covered: str, course_name: str) -> str:
        return (
            f"# {course_name} Notes\n\n"
            f"## Topics Covered\n{topics_covered}\n\n"
            "## Key Concepts\n- Core ideas extracted from the session topics\n\n"
            "## Detailed Explanations\n- Expand each topic with examples, formulas, and reasoning\n\n"
            "## Practice Questions\n1. Explain the topic in your own words.\n2. Solve a representative problem.\n"
        )

    def generate_assignment(self, payload: AssignmentGenerateRequest) -> tuple[str, list[dict]]:
        description = (
            f"AI-generated {payload.type} assignment for topics: {', '.join(payload.topics_covered)}.\n"
            "Include critical thinking, application-based prompts, and evaluation criteria."
        )
        questions: list[dict] = []
        if payload.type == "quiz":
            count = payload.num_questions or 5
            for index in range(1, count + 1):
                questions.append(
                    {
                        "question_text": f"Question {index} on {payload.topics_covered[(index - 1) % len(payload.topics_covered)]}",
                        "options": ["Option A", "Option B", "Option C", "Option D"],
                        "correct_answer": "Option A",
                        "points": 1,
                    }
                )
        return description, questions

    def grade_submission(
        self, assignment_type: str, description: str, text: str, rubric: Sequence[str], max_score: float
    ) -> dict:
        del description
        quality_factor = min(max(len(text.strip()) / 1000, 0.35), 0.95)
        score = round(max_score * quality_factor, 2)
        return {
            "score": score,
            "feedback": f"AI evaluation for {assignment_type} submission based on rubric alignment.",
            "strengths": ["Covers the primary concepts", "Shows structured thinking"],
            "improvements": ["Add more evidence", "Improve clarity in key sections"],
            "suggestions": ["Review rubric checkpoints", "Strengthen examples"],
            "focus_areas": list(rubric)[:3] or ["concept clarity", "presentation"],
        }

    def answer_course_question(self, content: str, context_type: str) -> str:
        return (
            f"AI response for {context_type} context.\n\n"
            f"Question: {content}\n\n"
            "This is where your retrieval-augmented answer pipeline would cite syllabus, notes, and uploaded documents."
        )

