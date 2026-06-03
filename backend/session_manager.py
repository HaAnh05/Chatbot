"""
Session Manager for handling conversation context and history
"""

from typing import List, Dict
from backend.database import SessionLocal
from backend.models import User, Conversation, Message, now_gmt7


class ConversationManager:
    """Manage conversation sessions and context"""

    def __init__(self):
        self.db = SessionLocal()

    def get_or_create_user(self, username: str = "guest") -> User:
        """Get existing user or create new one"""
        user = self.db.query(User).filter(User.username == username).first()
        if not user:
            user = User(username=username)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user

    def create_conversation(self, user_id: int, subject: str = "cpp", title: str = None) -> Conversation:
        """Create new conversation session"""
        if title is None:
            title = f"{subject.upper()} Conversation - {now_gmt7().strftime('%Y-%m-%d %H:%M')}"
        
        conversation = Conversation(user_id=user_id, subject=subject, title=title)
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def add_message(self, conversation_id: int, role: str, content: str) -> Message:
        """Add message to conversation history"""
        message = Message(conversation_id=conversation_id, role=role, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def get_conversation_history(self, conversation_id: int, limit: int = 10) -> List[Message]:
        """Retrieve conversation history (last N messages)"""
        messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.timestamp.desc())
            .limit(limit)
            .all()
        )
        return list(reversed(messages))  # Return in chronological order

    def format_context_for_llm(self, messages: List[Message]) -> str:
        """Format conversation history as context string for LLM"""
        context = ""
        for msg in messages:
            role = "Học sinh" if msg.role == "user" else "Trợ lý"
            context += f"{role}: {msg.content}\n\n"
        return context

    def get_user_conversations(self, user_id: int) -> List[Conversation]:
        """Get all conversations for a user"""
        conversations = (
            self.db.query(Conversation)
            .filter(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .all()
        )
        return conversations

    def delete_conversations(self, user_id: int, conversation_ids: List[int]) -> List[int]:
        """Delete conversations owned by a user and return deleted IDs."""
        if not conversation_ids:
            return []

        unique_ids = list(dict.fromkeys(conversation_ids))
        conversations = (
            self.db.query(Conversation)
            .filter(
                Conversation.user_id == user_id,
                Conversation.id.in_(unique_ids),
            )
            .all()
        )

        deleted_ids = [conversation.id for conversation in conversations]
        for conversation in conversations:
            self.db.delete(conversation)

        self.db.commit()
        return deleted_ids

    def close(self):
        """Close database session"""
        self.db.close()
