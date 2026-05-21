"""
Exercise Manager - Quiz, Flashcard, and Minigame generation and grading
"""

import json
import re
import time
from typing import Dict, List, Optional

import requests

from backend.config import LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT
from backend.database import SessionLocal
from backend.models import Exercise, ExerciseSubmission
from backend.logger import (
    get_logger,
    log_llm_request,
    log_llm_response,
    log_quiz_event,
    log_flashcard_event,
    log_minigame_event,
)

logger = get_logger("grader")


class ExerciseManager:
    """Generate and grade exercises using LLM"""

    def __init__(self):
        self.db = SessionLocal()
        self.model = LLM_MODEL
        self.base_url = LLM_BASE_URL
        self.timeout = None if LLM_TIMEOUT <= 0 else LLM_TIMEOUT
        logger.info(f"ExerciseManager initialized | model={self.model} | base_url={self.base_url}")

    def _call_llm(self, system_prompt: str, user_prompt: str) -> tuple:
        """
        Call LLM, trả về (content, reasoning_content).
        """
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
            "stream": False,
        }
        url = f"{self.base_url}/v1/chat/completions"

        log_llm_request(logger, self.model, payload["messages"], payload)

        logger.info(f"  Calling LLM at {url}")
        start_time = time.time()
        response = requests.post(url, json=payload, timeout=self.timeout)
        elapsed = time.time() - start_time
        response.raise_for_status()

        data = response.json()
        log_llm_response(logger, data, elapsed)

        choices = data.get("choices", [])
        if choices:
            message = choices[0].get("message", {})
            content = message.get("content", "").strip()
            reasoning = message.get("reasoning_content", "").strip()

            if reasoning:
                logger.info("THINKING PROCESS:")
                for line in reasoning.split("\n"):
                    if line.strip():
                        logger.info(f"  {line.strip()}")

            return content, reasoning

        raise ValueError("No response from LLM")

    def _parse_json_response(self, text: str) -> any:
        """Extract JSON from LLM response, handling markdown code fences"""
        logger.debug(f"Parsing JSON response ({len(text)} chars)")

        # Strip markdown code fences
        cleaned = text.strip()
        cleaned = re.sub(r"^```(?:json)?\s*\n?", "", cleaned)
        cleaned = re.sub(r"\n?```\s*$", "", cleaned)
        cleaned = cleaned.strip()

        # Try parsing the whole thing first
        try:
            result = json.loads(cleaned)
            logger.debug(f"  JSON parsed successfully: {type(result).__name__}")
            return result
        except json.JSONDecodeError:
            pass

        # Try to find a JSON array or object within the text
        for pattern in [r"\[[\s\S]*\]", r"\{[\s\S]*\}"]:
            match = re.search(pattern, cleaned)
            if match:
                try:
                    result = json.loads(match.group())
                    logger.debug(f"  JSON extracted via regex: {type(result).__name__}")
                    return result
                except json.JSONDecodeError:
                    continue

        logger.error(f"  Failed to parse JSON. Raw text: {text[:500]}")
        raise ValueError(f"Could not parse JSON from LLM response: {text[:200]}")

    def generate_quiz(
        self,
        subject: str,
        topic: str,
        difficulty: str = "beginner",
        count: int = 5,
    ) -> Dict:
        """Generate multiple-choice quiz questions via LLM"""
        log_quiz_event(logger, "Generating quiz", {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
            "count": count,
        })

        system_prompt = (
            "You are an educational quiz generator. "
            "Generate multiple-choice questions in JSON format. "
            "Output ONLY valid JSON, no markdown, no explanation."
        )
        user_prompt = (
            f"Generate {count} multiple-choice questions about '{topic}' "
            f"for {subject.upper()} programming (difficulty: {difficulty}).\n\n"
            "Return a JSON array with this exact structure:\n"
            '[{"question": "...", "options": ["A. ...", "B. ...", "C. ...", "D. ..."], '
            '"correct_index": 0, "explanation": "..."}]\n\n'
            "Questions should be in Vietnamese. "
            "correct_index is the 0-based index of the correct option. "
            f"Difficulty level: {difficulty}."
        )

        try:
            raw, reasoning = self._call_llm(system_prompt, user_prompt)

            log_quiz_event(logger, "LLM response received", {
                "raw_length": len(raw),
                "has_thinking": bool(reasoning),
            })

            questions = self._parse_json_response(raw)

            if not isinstance(questions, list):
                questions = [questions]

            # Store in database
            exercise = Exercise(
                subject=subject,
                topic=topic,
                title=f"Quiz: {topic}",
                description=f"Multiple choice quiz about {topic}",
                difficulty=difficulty,
                code_template="",
                test_cases=json.dumps(questions, ensure_ascii=False),
            )
            self.db.add(exercise)
            self.db.commit()
            self.db.refresh(exercise)

            log_quiz_event(logger, "Quiz saved to DB", {
                "exercise_id": exercise.id,
                "questions_count": len(questions),
            })

            # Return questions without answers for the client
            safe_questions = []
            for i, q in enumerate(questions):
                safe_questions.append({
                    "index": i,
                    "question": q.get("question", ""),
                    "options": q.get("options", []),
                    "explanation": q.get("explanation", ""),
                })

            result = {
                "exercise_id": exercise.id,
                "questions": safe_questions,
                "total": len(safe_questions),
            }

            log_quiz_event(logger, "Quiz generation complete", {
                "exercise_id": exercise.id,
                "total": len(safe_questions),
            })

            return result

        except Exception as e:
            self.db.rollback()
            log_quiz_event(logger, "Quiz generation FAILED", {"error": str(e)})
            raise RuntimeError(f"Failed to generate quiz: {str(e)}")

    def grade_quiz(
        self,
        exercise_id: int,
        user_id: int,
        answers: List[Dict],
    ) -> Dict:
        """Grade quiz answers against stored correct answers"""
        log_quiz_event(logger, "Grading quiz", {
            "exercise_id": exercise_id,
            "user_id": user_id,
            "answers_count": len(answers),
        })

        exercise = self.db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        questions = json.loads(exercise.test_cases)
        results = []
        score = 0

        for answer in answers:
            q_idx = answer.get("question_index", 0)
            selected = answer.get("selected_index", -1)
            if 0 <= q_idx < len(questions):
                correct = questions[q_idx].get("correct_index", 0)
                is_correct = selected == correct
                if is_correct:
                    score += 1
                results.append({
                    "question_index": q_idx,
                    "selected_index": selected,
                    "correct_index": correct,
                    "is_correct": is_correct,
                    "explanation": questions[q_idx].get("explanation", ""),
                })
                logger.debug(f"  Q{q_idx}: selected={selected}, correct={correct}, {'OK' if is_correct else 'WRONG'}")

        total = len(questions)
        all_correct = score == total

        # Store submission
        submission = ExerciseSubmission(
            exercise_id=exercise_id,
            user_id=user_id,
            submitted_code=json.dumps(answers, ensure_ascii=False),
            is_correct=all_correct,
            feedback=json.dumps({
                "score": score,
                "total": total,
                "results": results,
            }, ensure_ascii=False),
        )
        self.db.add(submission)
        self.db.commit()

        feedback_text = f"Đúng {score}/{total} câu."
        if score == total:
            feedback_text += " Xuất sắc!"
        elif score >= total * 0.7:
            feedback_text += " Khá tốt!"
        elif score >= total * 0.5:
            feedback_text += " Cần cố gắng thêm."
        else:
            feedback_text += " Hãy ôn tập lại nhé."

        log_quiz_event(logger, "Quiz graded", {
            "score": score,
            "total": total,
            "feedback": feedback_text,
        })

        return {
            "score": score,
            "total": total,
            "results": results,
            "feedback": feedback_text,
        }

    def generate_flashcards(
        self,
        subject: str,
        topic: str,
        count: int = 10,
    ) -> Dict:
        """Generate flashcards via LLM"""
        log_flashcard_event(logger, "Generating flashcards", {
            "subject": subject,
            "topic": topic,
            "count": count,
        })

        system_prompt = (
            "You are an educational flashcard generator. "
            "Generate flashcards in JSON format. "
            "Output ONLY valid JSON, no markdown, no explanation."
        )
        user_prompt = (
            f"Generate {count} flashcards about '{topic}' "
            f"for {subject.upper()} programming.\n\n"
            "Return a JSON array with this exact structure:\n"
            '[{"front": "Question or concept", "back": "Answer or explanation"}]\n\n'
            "Content should be in Vietnamese. "
            "Keep front concise (1-2 sentences). "
            "Keep back clear and informative (2-4 sentences)."
        )

        try:
            raw, reasoning = self._call_llm(system_prompt, user_prompt)

            log_flashcard_event(logger, "LLM response received", {
                "raw_length": len(raw),
                "has_thinking": bool(reasoning),
            })

            cards = self._parse_json_response(raw)

            if not isinstance(cards, list):
                cards = [cards]

            # Store in database
            exercise = Exercise(
                subject=subject,
                topic=topic,
                title=f"Flashcards: {topic}",
                description=f"Flashcard set about {topic}",
                difficulty="mixed",
                code_template="",
                test_cases=json.dumps(cards, ensure_ascii=False),
            )
            self.db.add(exercise)
            self.db.commit()
            self.db.refresh(exercise)

            log_flashcard_event(logger, "Flashcards saved to DB", {
                "exercise_id": exercise.id,
                "cards_count": len(cards),
            })

            return {
                "exercise_id": exercise.id,
                "cards": cards,
                "total": len(cards),
            }

        except Exception as e:
            self.db.rollback()
            log_flashcard_event(logger, "Flashcard generation FAILED", {"error": str(e)})
            raise RuntimeError(f"Failed to generate flashcards: {str(e)}")

    def start_minigame(
        self,
        subject: str,
        topic: str,
        difficulty: str = "beginner",
    ) -> Dict:
        """Generate a coding challenge via LLM"""
        log_minigame_event(logger, "Starting minigame", {
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
        })

        system_prompt = (
            "You are an educational coding challenge generator. "
            "Generate a coding challenge in JSON format. "
            "Output ONLY valid JSON, no markdown, no explanation."
        )
        user_prompt = (
            f"Generate a coding challenge about '{topic}' "
            f"for {subject.upper()} programming (difficulty: {difficulty}).\n\n"
            "Return a JSON object with this exact structure:\n"
            '{"title": "Challenge title", '
            '"description": "Clear description of what to implement", '
            '"starter_code": "Starter code template", '
            '"test_cases": [{"input": "test input", "expected_output": "expected output"}], '
            '"hints": ["hint 1", "hint 2"]}\n\n'
            "Content should be in Vietnamese. "
            "starter_code should be a valid code template. "
            "Include 2-3 test cases."
        )

        try:
            raw, reasoning = self._call_llm(system_prompt, user_prompt)

            log_minigame_event(logger, "LLM response received", {
                "raw_length": len(raw),
                "has_thinking": bool(reasoning),
            })

            challenge = self._parse_json_response(raw)

            # Store in database
            exercise = Exercise(
                subject=subject,
                topic=topic,
                title=challenge.get("title", f"Minigame: {topic}"),
                description=challenge.get("description", ""),
                difficulty=difficulty,
                code_template=challenge.get("starter_code", ""),
                test_cases=json.dumps(
                    challenge.get("test_cases", []),
                    ensure_ascii=False,
                ),
            )
            self.db.add(exercise)
            self.db.commit()
            self.db.refresh(exercise)

            log_minigame_event(logger, "Minigame saved to DB", {
                "exercise_id": exercise.id,
                "title": challenge.get("title", ""),
                "test_cases_count": len(challenge.get("test_cases", [])),
            })

            return {
                "exercise_id": exercise.id,
                "title": challenge.get("title", ""),
                "description": challenge.get("description", ""),
                "starter_code": challenge.get("starter_code", ""),
                "test_cases": challenge.get("test_cases", []),
                "hints": challenge.get("hints", []),
            }

        except Exception as e:
            self.db.rollback()
            log_minigame_event(logger, "Minigame generation FAILED", {"error": str(e)})
            raise RuntimeError(f"Failed to generate minigame: {str(e)}")

    def submit_minigame(
        self,
        exercise_id: int,
        user_id: int,
        submitted_code: str,
    ) -> Dict:
        """Evaluate submitted code against test cases using LLM"""
        log_minigame_event(logger, "Submitting minigame", {
            "exercise_id": exercise_id,
            "user_id": user_id,
            "code_length": len(submitted_code),
        })

        exercise = self.db.query(Exercise).filter(Exercise.id == exercise_id).first()
        if not exercise:
            raise ValueError(f"Exercise {exercise_id} not found")

        test_cases = json.loads(exercise.test_cases) if exercise.test_cases else []

        system_prompt = (
            "You are a code reviewer for an educational platform. "
            "Evaluate the student's code against the test cases. "
            "Output ONLY valid JSON, no markdown."
        )
        user_prompt = (
            f"Exercise: {exercise.title}\n"
            f"Description: {exercise.description}\n\n"
            f"Student's code:\n```\n{submitted_code}\n```\n\n"
            f"Test cases:\n{json.dumps(test_cases, ensure_ascii=False)}\n\n"
            "Return a JSON object:\n"
            '{"passed": true/false, "score": 0-100, '
            '"feedback": "Detailed feedback in Vietnamese", '
            '"test_results": [{"test": "description", "passed": true/false}]}'
        )

        try:
            raw, reasoning = self._call_llm(system_prompt, user_prompt)

            log_minigame_event(logger, "LLM evaluation received", {
                "raw_length": len(raw),
                "has_thinking": bool(reasoning),
            })

            result = self._parse_json_response(raw)

            # Store submission
            submission = ExerciseSubmission(
                exercise_id=exercise_id,
                user_id=user_id,
                submitted_code=submitted_code,
                is_correct=result.get("passed", False),
                feedback=json.dumps(result, ensure_ascii=False),
            )
            self.db.add(submission)
            self.db.commit()

            log_minigame_event(logger, "Minigame evaluated", {
                "passed": result.get("passed", False),
                "score": result.get("score", 0),
                "feedback_preview": result.get("feedback", "")[:100],
            })

            return {
                "passed": result.get("passed", False),
                "score": result.get("score", 0),
                "feedback": result.get("feedback", ""),
                "test_results": result.get("test_results", []),
            }

        except Exception as e:
            self.db.rollback()
            log_minigame_event(logger, "Minigame evaluation FAILED", {"error": str(e)})
            raise RuntimeError(f"Failed to evaluate code: {str(e)}")

    def close(self):
        """Close database session"""
        self.db.close()
        logger.debug("ExerciseManager session closed")
