"""
Engagement classification module with rules-based logic
This will be replaced with ML model in production
"""
from typing import Dict
from engagement_classifier.model import EngagementClassifierModel
from database.models import EngagementLevel


class EngagementClassifier:
    """
    Engagement classifier using rules-based logic
    Can be upgraded to use ML model when available
    """
    
    def __init__(self, use_ml_model: bool = False, model_path: str = None):
        """
        Initialize classifier
        
        Args:
            use_ml_model: Whether to use ML model (if loaded)
            model_path: Path to trained ML model
        """
        self.use_ml = use_ml_model
        self.ml_model = None
        
        if use_ml_model and model_path:
            self.ml_model = EngagementClassifierModel(model_path)
    
    def classify(
        self,
        response_time_ms: int,
        is_correct: bool,
        additional_context: Dict = None
    ) -> EngagementLevel:
        """
        Classify student engagement level
        
        Args:
            response_time_ms: Time taken to respond in milliseconds
            is_correct: Whether the answer was correct
            additional_context: Additional context (not used in rules-based)
        
        Returns:
            EngagementLevel enum: ACTIVE, MODERATE, or PASSIVE
        """
        # Use ML model if available
        if self.use_ml and self.ml_model and self.ml_model.is_loaded:
            return self._classify_with_ml(response_time_ms, is_correct, additional_context)
        
        # Otherwise use rules-based logic
        return self._classify_with_rules(response_time_ms, is_correct)
    
    def _classify_with_rules(self, response_time_ms: int, is_correct: bool) -> EngagementLevel:
        """
        Rules-based engagement classification
        
        Rules:
        - ACTIVE: response_time < 4000ms AND correct
        - MODERATE: response_time between 4000-7000ms (or correct)
        - PASSIVE: response_time > 7000ms OR wrong
        
        Args:
            response_time_ms: Response time in milliseconds
            is_correct: Whether answer was correct
        
        Returns:
            EngagementLevel
        """
        # Check for ACTIVE engagement
        if response_time_ms < 4000 and is_correct:
            return EngagementLevel.ACTIVE
        
        # Check for PASSIVE engagement
        if response_time_ms > 7000 or not is_correct:
            return EngagementLevel.PASSIVE
        
        # Otherwise MODERATE
        return EngagementLevel.MODERATE
    
    def _classify_with_ml(
        self,
        response_time_ms: int,
        is_correct: bool,
        additional_context: Dict
    ) -> EngagementLevel:
        """
        ML-based engagement classification
        
        Args:
            response_time_ms: Response time in milliseconds
            is_correct: Whether answer was correct
            additional_context: Additional context
        
        Returns:
            EngagementLevel
        """
        # Prepare features
        features = {
            'response_time_ms': response_time_ms,
            'is_correct': is_correct,
            **additional_context
        }
        
        # Get prediction from model
        prediction = self.ml_model.predict(features)
        
        # Convert to EngagementLevel enum
        return EngagementLevel[prediction.upper()]


def create_classifier(use_ml: bool = False, model_path: str = None) -> EngagementClassifier:
    """
    Factory function to create engagement classifier
    
    Args:
        use_ml: Whether to use ML model
        model_path: Path to model file
    
    Returns:
        EngagementClassifier instance
    """
    return EngagementClassifier(use_ml_model=use_ml, model_path=model_path)

