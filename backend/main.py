"""
Main FastAPI application entry point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from api import questions, engagement, sessions, responses, zoom, students
from database.db import init_db, engine, Base
from services.adaptive_engine import get_adaptive_engine
from websocket.student_ws import get_student_ws_manager
from websocket.instructor_ws import get_instructor_ws_manager
from zoom_integrator.zoom_events import get_zoom_event_handler
from sqlalchemy.orm import Session
import logging
from contextlib import asynccontextmanager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown tasks
    """
    # Startup
    logger.info("Initializing database...")
    init_db()
    
    logger.info("Initializing adaptive engine...")
    adaptive_engine = get_adaptive_engine()
    
    # Initialize adaptive engine with dependencies
    def get_db_session():
        from database.db import SessionLocal
        return SessionLocal()
    
    async def question_push_callback(session_id: int, student_ids: list):
        """
        Callback for adaptive engine to push questions to students
        
        This would integrate with the question generation service
        to deliver questions to students via WebSocket
        """
        student_ws = get_student_ws_manager()
        logger.info(f"Adaptive engine: pushing questions to {len(student_ids)} students in session {session_id}")
        
        # TODO: Get question from pool and send to students
        # For now, just log the action
    
    adaptive_engine.initialize(get_db_session, question_push_callback)
    adaptive_engine.start()
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down adaptive engine...")
    adaptive_engine.stop()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Engagement Classifier API",
    description="Real-Time Engagement Monitoring & Adaptive Question Delivery System",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(questions.router)
app.include_router(engagement.router)
app.include_router(sessions.router)
app.include_router(responses.router)
app.include_router(zoom.router)
app.include_router(students.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Engagement Classifier API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "API is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

