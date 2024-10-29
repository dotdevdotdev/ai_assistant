from core.interfaces.llm import LLMProvider
from typing import List, Dict, Optional


class CompositeLLMProvider(LLMProvider):
    def __init__(self, providers: Dict[str, LLMProvider]):
        self._providers = providers
        self._current_provider = next(iter(providers.values()))
        self._current_model = self._current_provider.get_default_model()

    def get_available_models(self) -> List[str]:
        models = []
        for provider_name, provider in self._providers.items():
            for model in provider.get_available_models():
                models.append(f"{provider_name}: {model}")
        return models

    def get_default_model(self) -> str:
        provider_name = next(iter(self._providers.keys()))
        return f"{provider_name}: {self._providers[provider_name].get_default_model()}"

    def set_model(self, model_name: str) -> None:
        provider_name, model = model_name.split(": ", 1)
        self._current_provider = self._providers[provider_name]
        self._current_provider.set_model(model)
        self._current_model = model_name

    def generate_response(
        self, message: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate response using current provider with optional system prompt"""
        return self._current_provider.generate_response(message, system_prompt)

    def get_providers(self) -> Dict[str, LLMProvider]:
        return self._providers
