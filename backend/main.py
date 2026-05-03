from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.database import SessionLocal, init_db
from backend.llm import EduAgent
from backend.models import Conversation, Message
from backend.session_manager import ConversationManager

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

        raw_reply = agent.ask(req.message, conversation_history=history_list)
        print("\n" + "=" * 50)
        print(f"RAW AI RESPONSE:\n{raw_reply}")
        print("=" * 50 + "\n")
        reply = raw_reply.strip()

        conv_manager.add_message(conversation.id, "user", req.message)
        conv_manager.add_message(conversation.id, "assistant", reply)

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

        conv_manager.close()

        return {
            "conversations": [
                {
                    "id": c.id,
                    "subject": c.subject,
                    "title": c.title,
                    "created_at": c.created_at.isoformat(),
                    "updated_at": c.updated_at.isoformat(),
                    "message_count": len(c.messages),
                }
                for c in conversations
            ]
        }
    except Exception as e:
        conv_manager.close()
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
