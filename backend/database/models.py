"""
SQLAlchemy database models for Engagement Classifier system
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from database.db import Base


class UserRole(str, enum.Enum):
    """User role enumeration"""
    STUDENT = "student"
    INSTRUCTOR = "instructor"


class EngagementLevel(str, enum.Enum):
    """Engagement level enumeration"""
    ACTIVE = "active"
    MODERATE = "moderate"
    PASSIVE = "passive"


class SessionStatus(str, enum.Enum):
    """Session status enumeration"""
    PENDING = "pending"
    ACTIVE = "active"
    ENDED = "ended"


class User(Base):
    """User model for students and instructors"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    student_id = Column(String(100), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    sessions = relationship("Session", back_populates="instructor")
    responses = relationship("Response", back_populates="student")
    engagement_logs = relationship("EngagementLog", back_populates="student")


class Question(Base):
    """Question model"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    correct_answer = Column(String(500), nullable=False)
    subject = Column(String(200))
    source_slide = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    generated_questions = relationship("GeneratedQuestion", back_populates="question")
    responses = relationship("Response", back_populates="question")


class Session(Base):
    """Session model for live classes"""
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    instructor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(SQLEnum(SessionStatus), default=SessionStatus.PENDING)
    zoom_meeting_id = Column(String(200), nullable=True)

    # Relationships
    instructor = relationship("User", back_populates="sessions")
    generated_questions = relationship("GeneratedQuestion", back_populates="session")
    responses = relationship("Response", back_populates="session")
    engagement_logs = relationship("EngagementLog", back_populates="session")


class GeneratedQuestion(Base):
    """Generated questions for a session"""
    __tablename__ = "generated_questions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    question = relationship("Question", back_populates="generated_questions")
    session = relationship("Session", back_populates="generated_questions")


class Response(Base):
    """Student responses to questions"""
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    response_text = Column(String(500), nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")
    session = relationship("Session", back_populates="responses")


class EngagementLog(Base):
    """Engagement level logs for students"""
    __tablename__ = "engagement_logs"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    engagement_level = Column(SQLEnum(EngagementLevel), nullable=False)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

    # Relationships
    student = relationship("User", back_populates="engagement_logs")
    session = relationship("Session", back_populates="engagement_logs")

