from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import SessionLocal, init_db
from backend.llm import EduAgent
from backend.models import Conversation, Message
from backend.session_manager import ConversationManager
from backend.grader import ExerciseManager
from backend.analytics import ProgressTracker
from backend.models import StudentProgress

# Load environment variables before creating local agents
load_dotenv()

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
    init_db()
    print("Database initialized")
    print("API ready at http://localhost:8000")


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
                user = conv_manager.get_or_create_user("guest")
                conversation = conv_manager.create_conversation(user.id, subject)
        else:
            user = conv_manager.get_or_create_user("guest")
            conversation = conv_manager.create_conversation(user.id, subject)

        history = conv_manager.get_conversation_history(conversation.id, limit=5)
        history_list = [{"role": m.role, "content": m.content} for m in history]

        raw_reply = agent.ask(req.message, conversation_history=history_list, image_base64=req.image_base64)
        print("\n" + "=" * 50)
        print(f"RAW AI RESPONSE:\n{raw_reply}")
        print("=" * 50 + "\n")
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
        return ChatResponse(reply=reply, conversation_id=conversation.id)

    except Exception as e:
        conv_manager.close()
        return ChatResponse(reply=f"Loi: {str(e)}", conversation_id=-1)


@app.post("/conversations", response_model=ConversationData)
async def create_conversation(req: ConversationCreate):
    """Create new conversation session."""
    conv_manager = ConversationManager()
    try:
        user = conv_manager.get_or_create_user("guest")
        conversation = conv_manager.create_conversation(
            user.id,
            subject=req.subject,
            title=req.title,
        )
        conv_manager.close()

        return ConversationData(
            id=conversation.id,
            subject=conversation.subject,
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            message_count=0,
        )
    except Exception:
        conv_manager.close()
        raise


@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: int):
    """Get conversation with all messages."""
    conv_manager = ConversationManager()
    try:
        db = SessionLocal()
        conversation = db.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()

        if not conversation:
            db.close()
            conv_manager.close()
            return {"error": "Conversation not found"}

        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.timestamp).all()

        db.close()
        conv_manager.close()

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
        return {"error": str(e)}


@app.get("/conversations")
async def list_conversations():
    """List all conversations for guest user."""
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

        return {"conversations": result}
    except Exception as e:
        conv_manager.close()
        return {"error": str(e)}


# ============ Quiz / Flashcard / Minigame / Progress Endpoints ============


@app.post("/quiz/generate")
async def generate_quiz(req: QuizGenerateRequest):
    """Generate quiz questions for a topic."""
    manager = ExerciseManager()
    try:
        result = manager.generate_quiz(req.subject, req.topic, req.difficulty, req.count)
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/quiz/submit")
async def submit_quiz(req: QuizSubmitRequest):
    """Submit quiz answers and get score."""
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
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/flashcard/generate")
async def generate_flashcards(req: FlashcardGenerateRequest):
    """Generate flashcards for a topic."""
    manager = ExerciseManager()
    try:
        result = manager.generate_flashcards(req.subject, req.topic, req.count)
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/minigame/start")
async def start_minigame(req: MinigameStartRequest):
    """Start a coding minigame challenge."""
    manager = ExerciseManager()
    try:
        result = manager.start_minigame(req.subject, req.topic, req.difficulty)
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        manager.close()


@app.post("/minigame/submit")
async def submit_minigame(req: MinigameSubmitRequest):
    """Submit minigame code for evaluation."""
    manager = ExerciseManager()
    try:
        result = manager.submit_minigame(req.exercise_id, req.user_id, req.submitted_code)
        return result
    except Exception as e:
        return {"error": str(e)}
    finally:
        manager.close()


@app.get("/progress/{user_id}")
async def get_progress(user_id: int, subject: Optional[str] = "cpp"):
    """Get student progress summary."""
    tracker = ProgressTracker()
    try:
        summary = tracker.get_progress_summary(user_id, subject)
        analytics = tracker.get_learning_analytics(user_id)
        return {"summary": summary, "analytics": analytics}
    except Exception as e:
        return {"error": str(e)}
    finally:
        tracker.close()


@app.post("/progress/update")
async def update_progress(user_id: int = 1, subject: str = "cpp", conversation_id: int = 0):
    """Manually update student progress."""
    tracker = ProgressTracker()
    try:
        progress = tracker.update_progress(user_id, subject, conversation_id)
        return {
            "user_id": progress.user_id,
            "subject": progress.subject,
            "confidence_level": progress.confidence_level,
            "total_conversations": progress.total_conversations,
            "total_exercises_completed": progress.total_exercises_completed,
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        tracker.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
