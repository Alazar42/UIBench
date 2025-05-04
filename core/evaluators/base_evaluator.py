from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseEvaluator(ABC):
    """Base class for all evaluators in the system."""
    
    def __init__(self, url: str, custom_criteria: Dict[str, Any] = None):
        self.url = url
        self.custom_criteria = custom_criteria or {}
    
    @abstractmethod
    async def evaluate(self) -> Dict[str, Any]:
        """Evaluate the target and return results."""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate the evaluation criteria and target."""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Clean up any resources used during evaluation."""
        pass 