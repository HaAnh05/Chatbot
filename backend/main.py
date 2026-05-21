from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import SessionLocal, init_db
from backend.llm import EduAgent
from backend.models import Conversation, Message
from backend.session_manager import ConversationManager
from backend.grader import ExerciseManager
from backend.analytics import ProgressTracker
from backend.models import StudentProgress
from backend.logger import get_logger

# Load environment variables before creating local agents
load_dotenv()

logger = get_logger("main")

app = FastAPI(title="Educational Chatbot API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    """Initialize database and agent on startup."""
    logger.info("Starting Educational Chatbot API...")
    init_db()
    logger.info("Database initialized")
    logger.info("API ready at http://localhost:8000")


agents = {
    "cpp": EduAgent(subject="cpp"),
    "python": EduAgent(subject="python"),
}


class ChatRequest(BaseModel):
    """Chat request model."""

    message: str
    subject: Optional[str] = "cpp"
    conversation_id: Optional[int] = None
    image_base64: Optional[str] = None


class ChatResponse(BaseModel):
    """Chat response model."""

    reply: str
    conversation_id: int


class ConversationCreate(BaseModel):
    """Create new conversation."""

    subject: Optional[str] = "cpp"
    title: Optional[str] = None


class ConversationData(BaseModel):
    """Conversation data model."""

    id: int
    subject: str
    title: str
    created_at: str
    message_count: int


class QuizGenerateRequest(BaseModel):
    subject: str = "cpp"
    topic: str
    difficulty: str = "beginner"
    count: int = 5


class QuizSubmitRequest(BaseModel):
    exercise_id: int
    user_id: int = 1
    answers: list


class FlashcardGenerateRequest(BaseModel):
    subject: str = "cpp"
    topic: str
    count: int = 10


class MinigameStartRequest(BaseModel):
    subject: str = "cpp"
    topic: str
    difficulty: str = "beginner"


class MinigameSubmitRequest(BaseModel):
    exercise_id: int
    user_id: int = 1
    submitted_code: str


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Chat endpoint - process user message and return AI response.
    Supports conversation history and multi-subject context.
    """
    logger.info(f"[CHAT] subject={req.subject} | conv_id={req.conversation_id} | "
                f"has_image={bool(req.image_base64)} | query={req.message[:80]}")

    subject = req.subject if req.subject in agents else "cpp"
    agent = agents[subject]

    conv_manager = ConversationManager()
    try:
        if req.conversation_id:
            db = SessionLocal()
            conversation = db.query(Conversation).filter(
                Conversation.id == req.conversation_id
            ).first()
            db.close()
            if not conversation:
                logger.warning(f"  Conversation {req.conversation_id} not found, creating new")
                user = conv_manager.get_or_create_user("guest")
                conversation = conv_manager.create_conversation(user.id, subject)
        else:
            user = conv_manager.get_or_create_user("guest")
            conversation = conv_manager.create_conversation(user.id, subject)

        history = conv_manager.get_conversation_history(conversation.id, limit=5)
        history_list = [{"role": m.role, "content": m.content} for m in history]
        logger.info(f"  History: {len(history_list)} messages")

        raw_reply = agent.ask(req.message, conversation_history=history_list, image_base64=req.image_base64)
        reply = raw_reply.strip()

        stored_message = req.message
        if req.image_base64:
            stored_message = req.message + "\n[image attached]"
        conv_manager.add_message(conversation.id, "user", stored_message)
        conv_manager.add_message(conversation.id, "assistant", reply)

        # Update progress (non-blocking)
        try:
            user = conv_manager.get_or_create_user("guest")
            tracker = ProgressTracker()
            tracker.update_progress(user.id, subject, conversation.id)
        except Exception:
            pass

        conv_manager.close()
        logger.info(f"[CHAT] Done | conv_id={conversation.id} | reply_len={len(reply)}")
        return ChatResponse(reply=reply, conversation_id=conversation.id)

    except Exception as e:
        conv_manager.close()
        logger.error(f"[CHAT] ERROR: {e}", exc_info=True)
        return ChatResponse(reply=f"Loi: {str(e)}", conversation_id=-1)


@app.post("/conversations", response_model=ConversationData)
async def create_conversation(req: ConversationCreate):
    """Create new conversation session."""
    logger.info(f"[CONV] Creating conversation | subject={req.subject}")
    conv_manager = ConversationManager()
    try:
        user = conv_manager.get_or_create_user("guest")
        conversation = conv_manager.create_conversation(
            user.id,
            subject=req.subject,
            title=req.title,
        )
        conv_manager.close()

        logger.info(f"[CONV] Created | id={conversation.id} | title={conversation.title}")
        return ConversationData(
            id=conversation.id,
            subject=conversation.subject,
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            message_count=0,
        )
    except Exception:
        conv_manager.close()
        logger.error(f"[CONV] Create failed", exc_info=True)
        raise


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get conversation with all messages."""
    logger.info(f"[CONV] Getting conversation {conversation_id}")
    conv_manager = ConversationManager()
    try:
        db = SessionLocal()
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            db.close()
            conv_manager.close()
            logger.warning(f"[CONV] Conversation {conversation_id} not found")
            return {"error": "Conversation not found"}

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()

        db.close()
        conv_manager.close()

        logger.info(f"[CONV] Found {len(messages)} messages")
        return {
            "id": conversation.id,
            "subject": conversation.subject,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "role": m.role,
                    "content": m.content,
                    "timestamp": m.timestamp.isoformat(),
                }
                for m in messages
            ],
        }
    except Exception as e:
        conv_manager.close()
        logger.error(f"[CONV] Get failed: {e}", exc_info=True)
        return {"error": str(e)}


@app.get("/conversations")
async def list_conversations():
    """List all conversations for guest user."""
    logger.info("[CONV] Listing conversations")
    conv_manager = ConversationManager()
    try:
        user = conv_manager.get_or_create_user("guest")
        conversations = conv_manager.get_user_conversations(user.id)

        result = []
        for c in conversations:
            msg_count = len(c.messages)
            result.append({
                "id": c.id,
                "subject": c.subject,
                "title": c.title,
                "created_at": c.created_at.isoformat(),
                "updated_at": c.updated_at.isoformat(),
                "message_count": msg_count,
            })

        conv_manager.close()
        logger.info(f"[CONV] Found {len(result)} conversations")
        return {"conversations": result}
    except Exception as e:
        conv_manager.close()
        logger.error(f"[CONV] List failed: {e}", exc_info=True)
        return {"error": str(e)}


# ============ Quiz / Flashcard / Minigame / Progress Endpoints ============


@app.post("/quiz/generate")
async def generate_quiz(req: QuizGenerateRequest):
    """Generate quiz questions for a topic."""
    logger.info(f"[API] POST /quiz/generate | subject={req.subject} | topic={req.topic} | "
                f"difficulty={req.difficulty} | count={req.count}")
    manager = ExerciseManager()
    try:
        result = manager.generate_quiz(req.subject, req.topic, req.difficulty, req.count)
        logger.info(f"[API] Quiz generated | exercise_id={result.get('exercise_id')} | total={result.get('total')}")
        return result
    except Exception as e:
        logger.error(f"[API] Quiz generate failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/quiz/submit")
async def submit_quiz(req: QuizSubmitRequest):
    """Submit quiz answers and get score."""
    logger.info(f"[API] POST /quiz/submit | exercise_id={req.exercise_id} | user_id={req.user_id}")
    manager = ExerciseManager()
    try:
        result = manager.grade_quiz(req.exercise_id, req.user_id, req.answers)
        # Update exercise completion count
        try:
            db = SessionLocal()
            progress = db.query(StudentProgress).filter(
                StudentProgress.user_id == req.user_id
            ).first()
            if progress:
                progress.total_exercises_completed += 1
                db.commit()
            db.close()
        except Exception:
            pass
        logger.info(f"[API] Quiz graded | score={result.get('score')}/{result.get('total')}")
        return result
    except Exception as e:
        logger.error(f"[API] Quiz submit failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/flashcard/generate")
async def generate_flashcards(req: FlashcardGenerateRequest):
    """Generate flashcards for a topic."""
    logger.info(f"[API] POST /flashcard/generate | subject={req.subject} | topic={req.topic} | count={req.count}")
    manager = ExerciseManager()
    try:
        result = manager.generate_flashcards(req.subject, req.topic, req.count)
        logger.info(f"[API] Flashcards generated | exercise_id={result.get('exercise_id')} | total={result.get('total')}")
        return result
    except Exception as e:
        logger.error(f"[API] Flashcard generate failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/minigame/start")
async def start_minigame(req: MinigameStartRequest):
    """Start a coding minigame challenge."""
    logger.info(f"[API] POST /minigame/start | subject={req.subject} | topic={req.topic} | difficulty={req.difficulty}")
    manager = ExerciseManager()
    try:
        result = manager.start_minigame(req.subject, req.topic, req.difficulty)
        logger.info(f"[API] Minigame started | exercise_id={result.get('exercise_id')} | title={result.get('title')}")
        return result
    except Exception as e:
        logger.error(f"[API] Minigame start failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/minigame/submit")
async def submit_minigame(req: MinigameSubmitRequest):
    """Submit minigame code for evaluation."""
    logger.info(f"[API] POST /minigame/submit | exercise_id={req.exercise_id} | user_id={req.user_id} | "
                f"code_len={len(req.submitted_code)}")
    manager = ExerciseManager()
    try:
        result = manager.submit_minigame(req.exercise_id, req.user_id, req.submitted_code)
        logger.info(f"[API] Minigame evaluated | passed={result.get('passed')} | score={result.get('score')}")
        return result
    except Exception as e:
        logger.error(f"[API] Minigame submit failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        manager.close()


@app.get("/progress/{user_id}")
async def get_progress(user_id: int, subject: Optional[str] = "cpp"):
    """Get student progress summary."""
    logger.info(f"[API] GET /progress/{user_id} | subject={subject}")
    tracker = ProgressTracker()
    try:
        summary = tracker.get_progress_summary(user_id, subject)
        analytics = tracker.get_learning_analytics(user_id)
        logger.info(f"[API] Progress loaded | confidence={summary.get('confidence_level')} | "
                     f"conversations={summary.get('total_conversations')}")
        return {"summary": summary, "analytics": analytics}
    except Exception as e:
        logger.error(f"[API] Progress get failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        tracker.close()


@app.post("/progress/update")
async def update_progress(user_id: int = 1, subject: str = "cpp", conversation_id: int = 0):
    """Manually update student progress."""
    logger.info(f"[API] POST /progress/update | user_id={user_id} | subject={subject}")
    tracker = ProgressTracker()
    try:
        progress = tracker.update_progress(user_id, subject, conversation_id)
        logger.info(f"[API] Progress updated | confidence={progress.confidence_level}")
        return {
            "user_id": progress.user_id,
            "subject": progress.subject,
            "confidence_level": progress.confidence_level,
            "total_conversations": progress.total_conversations,
            "total_exercises_completed": progress.total_exercises_completed,
        }
    except Exception as e:
        logger.error(f"[API] Progress update failed: {e}", exc_info=True)
        return {"error": str(e)}
    finally:
        tracker.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
