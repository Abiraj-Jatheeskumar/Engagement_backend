"""
Data preprocessing for engagement classification
Prepares student data for model input
"""
from typing import Dict, List
import numpy as np


def extract_features(data: Dict) -> Dict:
    """
    Extract relevant features from raw student data
    
    Args:
        data: Dictionary containing student metrics
            {
                'response_time_ms': int,
                'is_correct': bool,
                'question_difficulty': float,
                'attempt_count': int,
                'avg_response_time': float
            }
    
    Returns:
        Dictionary of extracted features
    """
    features = {
        'response_time': data.get('response_time_ms', 0),
        'is_correct': 1.0 if data.get('is_correct', False) else 0.0,
        'question_difficulty': data.get('question_difficulty', 0.5),
        'attempt_count': data.get('attempt_count', 1),
        'avg_response_time': data.get('avg_response_time', 5000.0)
    }
    
    return features


def normalize_features(features: Dict) -> np.ndarray:
    """
    Normalize features to [0, 1] range for model input
    
    Args:
        features: Dictionary of feature values
    
    Returns:
        Normalized numpy array
    """
    # Define normalization ranges for each feature
    normalization_params = {
        'response_time': (0, 10000),  # 0-10 seconds
        'is_correct': (0, 1),
        'question_difficulty': (0, 1),
        'attempt_count': (0, 10),
        'avg_response_time': (0, 10000)
    }
    
    normalized = []
    for key, (min_val, max_val) in normalization_params.items():
        value = features.get(key, 0)
        norm_value = (value - min_val) / (max_val - min_val)
        norm_value = max(0, min(1, norm_value))  # Clip to [0, 1]
        normalized.append(norm_value)
    
    return np.array(normalized)


def prepare_batch(students_data: List[Dict]) -> np.ndarray:
    """
    Prepare batch of student data for model inference
    
    Args:
        students_data: List of student data dictionaries
    
    Returns:
        Batch numpy array of shape (num_students, num_features)
    """
    batch = []
    for student_data in students_data:
        features = extract_features(student_data)
        normalized = normalize_features(features)
        batch.append(normalized)
    
    return np.array(batch)


def interpret_prediction(prediction: np.ndarray) -> str:
    """
    Convert model prediction to engagement level string
    
    Args:
        prediction: Model output (could be probability distribution or logits)
    
    Returns:
        Engagement level: "active", "moderate", or "passive"
    """
    # Handle different prediction formats
    if len(prediction.shape) == 2:
        # Multiple predictions (batch)
        engagement_levels = []
        for pred in prediction:
            idx = np.argmax(pred)
            level = ["active", "moderate", "passive"][idx]
            engagement_levels.append(level)
        return engagement_levels
    else:
        # Single prediction
        idx = np.argmax(prediction)
        level = ["active", "moderate", "passive"][idx]
        return level

