"""
SQLAlchemy ORM Models for conversation persistence and progress tracking
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from backend.database import Base

GMT7 = timezone(timedelta(hours=7))


def now_gmt7():
    return datetime.now(GMT7).replace(tzinfo=None)


class User(Base):
    """Student/User profile"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime, default=now_gmt7)
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    progress = relationship("StudentProgress", back_populates="user", uselist=False, cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"


class Conversation(Base):
    """Chat conversation session"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    subject = Column(String(50), default="cpp")  # cpp, python, web, etc.
    title = Column(String(200), default="Untitled Conversation")
    created_at = Column(DateTime, default=now_gmt7)
    updated_at = Column(DateTime, default=now_gmt7, onupdate=now_gmt7)
    
    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")

    def __repr__(self):
        return f"<Conversation(id={self.id}, subject='{self.subject}', user_id={self.user_id})>"


class Message(Base):
    """Individual chat message"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), index=True)
    role = Column(String(10))  # 'user' or 'assistant'
    content = Column(Text)  # Message text
    timestamp = Column(DateTime, default=now_gmt7, index=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}', timestamp={self.timestamp})>"


class StudentProgress(Base):
    """Track student learning progress"""
    __tablename__ = "student_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, index=True)
    subject = Column(String(50))  # cpp, python, etc.
    topics_covered = Column(Text)  # JSON string of topics studied
    confidence_level = Column(Float, default=0.0)  # 0.0 - 1.0
    total_conversations = Column(Integer, default=0)
    total_exercises_completed = Column(Integer, default=0)
    last_updated = Column(DateTime, default=now_gmt7, onupdate=now_gmt7)
    
    # Relationships
    user = relationship("User", back_populates="progress")

    def __repr__(self):
        return f"<StudentProgress(user_id={self.user_id}, subject='{self.subject}', confidence={self.confidence_level})>"


class Exercise(Base):
    """Practice exercises for students"""
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    subject = Column(String(50), index=True)  # cpp, python, web, etc.
    topic = Column(String(100), index=True)  # for loop, functions, classes, etc.
    title = Column(String(200))
    description = Column(Text)
    difficulty = Column(String(20))  # beginner, intermediate, advanced
    code_template = Column(Text)  # Template code for students
    test_cases = Column(Text)  # JSON string with expected inputs/outputs
    created_at = Column(DateTime, default=now_gmt7)
    
    # Relationships
    submissions = relationship("ExerciseSubmission", back_populates="exercise", cascade="all, delete")

    def __repr__(self):
        return f"<Exercise(id={self.id}, subject='{self.subject}', topic='{self.topic}')>"


class ExerciseSubmission(Base):
    """Track student exercise submissions"""
    __tablename__ = "exercise_submissions"

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    submitted_code = Column(Text)
    is_correct = Column(Boolean, default=False)
    feedback = Column(Text)  # Grading feedback
    submitted_at = Column(DateTime, default=now_gmt7)
    
    # Relationships
    exercise = relationship("Exercise", back_populates="submissions")

    def __repr__(self):
        return f"<ExerciseSubmission(user_id={self.user_id}, exercise_id={self.exercise_id}, correct={self.is_correct})>"
