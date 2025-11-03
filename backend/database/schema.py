"""
Pydantic schemas for request/response validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from database.models import UserRole, EngagementLevel, SessionStatus


# User Schemas
class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: UserRole
    student_id: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Question Schemas
class QuestionBase(BaseModel):
    text: str
    correct_answer: str
    subject: Optional[str] = None
    source_slide: Optional[str] = None


class QuestionCreate(QuestionBase):
    pass


class QuestionResponse(QuestionBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Session Schemas
class SessionBase(BaseModel):
    instructor_id: int
    zoom_meeting_id: Optional[str] = None


class SessionCreate(SessionBase):
    pass


class SessionResponse(BaseModel):
    id: int
    instructor_id: int
    start_time: datetime
    end_time: Optional[datetime]
    status: SessionStatus
    zoom_meeting_id: Optional[str]

    class Config:
        from_attributes = True


# Response Schemas
class ResponseCreate(BaseModel):
    student_id: int
    question_id: int
    session_id: int
    response_text: str
    response_time_ms: int


class ResponseResponse(BaseModel):
    id: int
    student_id: int
    question_id: int
    session_id: int
    response_text: str
    response_time_ms: int
    is_correct: bool
    timestamp: datetime

    class Config:
        from_attributes = True


# Engagement Schemas
class EngagementLogResponse(BaseModel):
    id: int
    student_id: int
    engagement_level: EngagementLevel
    session_id: int
    timestamp: datetime

    class Config:
        from_attributes = True


class EngagementUpdate(BaseModel):
    student_id: int
    engagement_level: EngagementLevel


# Dashboard Schemas
class DashboardStats(BaseModel):
    total_students: int
    active_students: int
    moderate_students: int
    passive_students: int
    total_questions: int
    total_responses: int


class StudentEngagementStatus(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    current_engagement: EngagementLevel
    response_count: int
    correct_count: int
    avg_response_time: float


class SessionDetails(BaseModel):
    session: SessionResponse
    stats: DashboardStats
    students: List[StudentEngagementStatus]


# WebSocket Schemas
class QuestionMessage(BaseModel):
    type: str = "question"
    question_id: int
    question_text: str
    question_subject: Optional[str]
    session_id: int


class ResponseMessage(BaseModel):
    type: str = "response"
    student_id: int
    question_id: int
    is_correct: bool


class EngagementMessage(BaseModel):
    type: str = "engagement"
    student_id: int
    engagement_level: EngagementLevel


class DashboardUpdate(BaseModel):
    type: str = "dashboard_update"
    stats: DashboardStats
    students: List[StudentEngagementStatus]

