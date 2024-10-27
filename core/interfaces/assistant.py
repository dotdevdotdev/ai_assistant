from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional, Dict, Any


class Message:
    def __init__(self, role: str, content: str):
        self.role = role
        self.content = content


class AssistantProvider(ABC):
    @abstractmethod
    async def send_message(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[str]:
        """Send a message to the AI assistant and get streaming response"""
        pass

    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available AI models"""
        pass

    @abstractmethod
    async def get_model_config(self, model_name: str) -> Dict[str, Any]:
        """Get configuration options for a specific model"""
        pass
