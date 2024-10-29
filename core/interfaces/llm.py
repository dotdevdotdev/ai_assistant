from abc import ABC, abstractmethod
from typing import List, Dict, Optional


class LLMProvider(ABC):
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Return list of available model names with provider prefix"""
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """Return the default model name with provider prefix"""
        pass

    @abstractmethod
    def set_model(self, model_name: str) -> None:
        """Set the active model (expects provider:model format)"""
        pass

    @abstractmethod
    def generate_response(
        self, message: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a response to the given message, optionally using a system prompt"""
        pass

    @abstractmethod
    def get_providers(self) -> Dict[str, "LLMProvider"]:
        """Return dictionary of available providers"""
        pass
