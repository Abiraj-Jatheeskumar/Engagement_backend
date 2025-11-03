"""
Question generation module with mock ML function
This module will be replaced with actual ML model in production
"""
import random
from typing import List, Dict
from datetime import datetime


class Question:
    """Question data structure"""
    def __init__(self, text: str, correct_answer: str, source_slide: int = None):
        self.text = text
        self.correct_answer = correct_answer
        self.source_slide = source_slide


def generate_questions_mock(text_chunks: List[str], num_questions: int = 5) -> List[Dict]:
    """
    Mock question generation function that mimics future ML model
    
    This function generates dummy questions based on text chunks.
    In production, this will be replaced with actual ML/NLP model.
    
    Args:
        text_chunks: List of extracted text chunks from slides
        num_questions: Number of questions to generate
    
    Returns:
        List of question dictionaries with structure:
        {
            'text': str,
            'correct_answer': str,
            'source_slide': int
        }
    """
    if not text_chunks:
        return []
    
    questions = []
    question_templates = [
        "What is the main topic discussed in this lecture?",
        "Which concept is most important in this section?",
        "What is a key takeaway from this material?",
        "Explain the primary concept discussed.",
        "What would be the best application of this knowledge?",
        "What problem does this solution address?",
        "How does this concept relate to real-world scenarios?",
        "What are the key components of this topic?",
        "Why is this concept significant?",
        "What are the implications of this discussion?"
    ]
    
    answer_templates = [
        "The main topic is covered in the lecture material.",
        "This is a key concept in the subject.",
        "The primary takeaway is the understanding of fundamentals.",
        "This concept is essential for advanced learning.",
        "The best application is in practical scenarios.",
        "This solution addresses common problems.",
        "It relates directly to practical implementations.",
        "The key components are comprehensively covered.",
        "This concept is significant for understanding the topic.",
        "The implications are far-reaching and important."
    ]
    
    # Generate questions based on number of text chunks
    for i in range(min(num_questions, len(text_chunks))):
        template_idx = i % len(question_templates)
        slide_idx = i % len(text_chunks)
        
        question_text = f"{question_templates[template_idx]} (Based on Slide {slide_idx + 1})"
        correct_answer = f"{answer_templates[template_idx]} (Slide {slide_idx + 1})"
        
        questions.append({
            'text': question_text,
            'correct_answer': correct_answer,
            'source_slide': slide_idx
        })
    
    return questions


def prepare_text_for_model(text_chunks: List[str]) -> str:
    """
    Prepare and combine text chunks for ML model input
    
    Args:
        text_chunks: List of text chunks
    
    Returns:
        Combined and formatted text string
    """
    combined_text = "\n\n---SLIDE_SEPARATOR---\n\n".join(text_chunks)
    return combined_text


# Future: This will load and use actual ML model
def load_question_model(model_path: str = None):
    """
    Placeholder for loading actual ML model
    
    Args:
        model_path: Path to trained model
    
    Returns:
        Model object (currently returns None)
    """
    # TODO: Implement actual model loading
    # model = load_model(model_path)
    # return model
    return None


# Future: This will use actual ML model for generation
def generate_questions_with_model(model, text: str) -> List[Dict]:
    """
    Generate questions using actual ML model
    
    Args:
        model: Trained ML model
        text: Input text
    
    Returns:
        List of generated questions
    """
    # TODO: Implement actual model inference
    # questions = model.generate(text)
    # return questions
    pass

