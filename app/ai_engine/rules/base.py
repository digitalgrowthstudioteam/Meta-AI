from abc import ABC, abstractmethod
from typing import List

from app.ai_engine.models.action_models import AIAction


class BaseRule(ABC):
    """
    Base interface for all AI rules.
    """

    @abstractmethod
    async def evaluate(self, *args, **kwargs) -> List[AIAction]:
        """
        Evaluate rule and return zero or more AIAction objects.
        """
        raise NotImplementedError
