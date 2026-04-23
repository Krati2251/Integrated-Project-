"""
Quiz API Integration Module

Provides FastAPI endpoints for quiz generation and scoring
Integrates with Groq LLM client for dynamic question generation
"""

import os
import json
from typing import Dict
from fastapi import APIRouter, HTTPException
from dotenv import load_dotenv
import logging
from pydantic import BaseModel

load_dotenv()

logger = logging.getLogger("quiz_api")

quiz_router = APIRouter(prefix="/quiz", tags=["quiz"])


class QuizScoreRequest(BaseModel):
    question_id: int
    selected_option: str
    quiz_data: Dict


class QuizEngine:
    """Core quiz engine using Groq LLM"""
    
    def __init__(self):
        try:
            from groq import Groq
            self.client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
            self.model = os.getenv("QUIZ_MODEL", "llama-3.3-70b-versatile")
            self.temperature = float(os.getenv("QUIZ_TEMPERATURE", "0.9"))
            self.top_p = float(os.getenv("QUIZ_TOP_P", "0.92"))
            self.max_tokens = int(os.getenv("QUIZ_MAX_TOKENS", "2200"))
        except ImportError:
            logger.warning("Groq not installed, quiz will use mock mode")
            self.client = None
    
    def generate_quiz(self, topic: str = "Finance", num_questions: int = 5) -> Dict:
        """
        Generate a quiz dynamically using Groq LLM.
        
        Args:
            topic: Quiz topic (default: Finance)
            num_questions: Number of questions to generate
            
        Returns:
            Dictionary with questions and metadata
        """
        if not self.client:
            return self._mock_quiz(num_questions)
        
        try:
            system_prompt = (
                "You are an expert quiz designer for finance education. "
                "Your output must be valid JSON only, with no markdown wrappers. "
                "Create original, non-repetitive questions with varied style."
            )

            prompt = f"""Generate exactly {num_questions} multiple-choice quiz questions on this topic: {topic}.

Hard requirements:
1) Every question must test a DIFFERENT concept. No repeated concept or template.
2) Vary phrasing style across questions (scenario, calculation, definition, comparison, risk analysis).
3) Options must be unique per question and plausible distractors.
4) Exactly one option has \"correct\": true.
5) Correct option position must vary across questions (not always first).
6) Keep explanations concise and specific.

Return JSON with this exact structure:
{{
  "questions": [
    {{
      "id": 1,
      "question": "Question text?",
      "options": [
        {{"text": "Option A", "correct": false}},
        {{"text": "Option B", "correct": true}},
        {{"text": "Option C", "correct": false}},
        {{"text": "Option D", "correct": false}}
      ],
      "explanation": "Short explanation"
    }}
  ]
}}

Do not return any keys other than: questions, id, question, options, text, correct, explanation."""

            message = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
            )
            
            response_text = message.choices[0].message.content
            
            # Extract JSON from response
            try:
                quiz_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON from markdown code blocks
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                    quiz_data = json.loads(json_str)
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                    quiz_data = json.loads(json_str)
                else:
                    raise ValueError("Could not parse JSON from LLM response")
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error generating quiz: {e}")
            return self._mock_quiz(num_questions)
    
    def _mock_quiz(self, num_questions: int = 5) -> Dict:
        """Return mock quiz for testing"""
        questions = [
            {
                "id": i + 1,
                "question": f"Sample Finance Question {i + 1}?",
                "options": [
                    {"text": "Option A", "correct": (i % 4) == 0},
                    {"text": "Option B", "correct": (i % 4) == 1},
                    {"text": "Option C", "correct": (i % 4) == 2},
                    {"text": "Option D", "correct": (i % 4) == 3}
                ],
                "explanation": "This is the correct option based on the finance concept in the question."
            }
            for i in range(min(num_questions, 5))
        ]
        
        return {"questions": questions}
    
    def score_answer(self, question_id: int, selected_option: str, quiz_data: Dict) -> Dict:
        """
        Score a user's answer.
        
        Args:
            question_id: Question ID (1-indexed)
            selected_option: Text of selected option
            quiz_data: The quiz data containing correct answers
            
        Returns:
            Dictionary with is_correct, explanation, etc.
        """
        try:
            if "questions" not in quiz_data:
                raise ValueError("Invalid quiz data structure")
            
            question = next(
                (q for q in quiz_data["questions"] if q["id"] == question_id),
                None
            )
            
            if not question:
                raise ValueError(f"Question {question_id} not found")
            
            correct_option = next(
                (opt for opt in question["options"] if opt.get("correct")),
                None
            )
            
            if not correct_option:
                raise ValueError("No correct option marked in question")
            
            is_correct = selected_option == correct_option["text"]
            
            return {
                "is_correct": is_correct,
                "selected": selected_option,
                "correct_answer": correct_option["text"],
                "explanation": question.get("explanation", ""),
                "points": 1 if is_correct else 0
            }
            
        except Exception as e:
            logger.error(f"Error scoring answer: {e}")
            raise HTTPException(status_code=400, detail=str(e))


# Initialize quiz engine
quiz_engine = QuizEngine()


@quiz_router.get("/generate")
async def generate_quiz(topic: str = "Finance", num_questions: int = 5) -> Dict:
    """
    Generate a new quiz.
    
    Query Parameters:
    - topic: Quiz topic (default: Finance)
    - num_questions: Number of questions (1-10, default: 5)
    """
    if num_questions < 1 or num_questions > 10:
        raise HTTPException(status_code=400, detail="num_questions must be between 1 and 10")
    
    try:
        quiz = quiz_engine.generate_quiz(topic, num_questions)
        return {
            "status": "success",
            "data": quiz
        }
    except Exception as e:
        logger.error(f"Error in /quiz/generate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@quiz_router.post("/score")
async def score_answer(payload: QuizScoreRequest) -> Dict:
    """
    Score a user's answer.
    
    Body Parameters:
    - question_id: Question ID
    - selected_option: Text of selected option
    - quiz_data: Complete quiz data
    """
    result = quiz_engine.score_answer(
        payload.question_id,
        payload.selected_option,
        payload.quiz_data,
    )
    return {
        "status": "success",
        "data": result
    }


@quiz_router.get("/health")
async def quiz_health() -> Dict:
    """Health check for quiz service"""
    return {
        "status": "healthy",
        "service": "quiz",
        "llm_available": quiz_engine.client is not None,
        "model": getattr(quiz_engine, "model", None),
        "temperature": getattr(quiz_engine, "temperature", None),
        "top_p": getattr(quiz_engine, "top_p", None),
    }
