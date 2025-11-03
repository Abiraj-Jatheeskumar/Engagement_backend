"""
API routes for question management
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database.db import get_db
from database import models, schema
from database.schema import QuestionResponse, QuestionCreate
from services.text_extractor import extract_text_by_type
from services.question_generator import generate_questions_mock
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/questions", tags=["questions"])


@router.post("/upload-slides", response_model=List[QuestionResponse])
async def upload_slides_and_generate_questions(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload lecture slides and generate questions
    
    Args:
        file: PDF or PPTX file
        db: Database session
    
    Returns:
        List of generated questions
    """
    try:
        # Read file content
        file_content = await file.read()
        file_type = file.content_type
        
        # Extract text from slides
        logger.info(f"Extracting text from {file.filename} (type: {file_type})")
        text_chunks = extract_text_by_type(file_content, file_type)
        
        if not text_chunks:
            raise HTTPException(status_code=400, detail="No text extracted from file")
        
        # Generate questions using mock function
        logger.info(f"Generating questions from {len(text_chunks)} text chunks")
        generated_questions = generate_questions_mock(text_chunks, num_questions=min(10, len(text_chunks)))
        
        # Save questions to database
        saved_questions = []
        for i, q_data in enumerate(generated_questions):
            question = models.Question(
                text=q_data['text'],
                correct_answer=q_data['correct_answer'],
                source_slide=f"{file.filename} - Slide {q_data.get('source_slide', i) + 1}",
                subject="Lecture Material"  # Can be extracted from file metadata
            )
            db.add(question)
            db.commit()
            db.refresh(question)
            saved_questions.append(question)
        
        logger.info(f"Successfully generated {len(saved_questions)} questions")
        return saved_questions
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating questions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate questions")


@router.get("/", response_model=List[QuestionResponse])
async def get_all_questions(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get all questions
    
    Args:
        skip: Number of questions to skip
        limit: Maximum number of questions to return
        db: Database session
    
    Returns:
        List of questions
    """
    questions = db.query(models.Question).offset(skip).limit(limit).all()
    return questions


@router.get("/{question_id}", response_model=QuestionResponse)
async def get_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific question by ID
    
    Args:
        question_id: Question ID
        db: Database session
    
    Returns:
        Question details
    """
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    return question


@router.post("/", response_model=QuestionResponse)
async def create_question(
    question: QuestionCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new question manually
    
    Args:
        question: Question data
        db: Database session
    
    Returns:
        Created question
    """
    db_question = models.Question(**question.dict())
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    
    logger.info(f"Created question {db_question.id}")
    return db_question


@router.delete("/{question_id}")
async def delete_question(
    question_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a question
    
    Args:
        question_id: Question ID
        db: Database session
    """
    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    db.delete(question)
    db.commit()
    
    logger.info(f"Deleted question {question_id}")
    return {"message": "Question deleted successfully"}

