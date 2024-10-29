from core.interfaces.llm import LLMProvider
from anthropic import Anthropic
import os
from typing import Dict


class AnthropicProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._current_model = self.get_default_model()

    def get_available_models(self):
        return self._config.models

    def get_default_model(self):
        return self._config.default_model

    def set_model(self, model_name: str):
        if model_name not in self.get_available_models():
            raise ValueError(f"Unknown model: {model_name}")
        self._current_model = model_name

    def generate_response(self, message: str) -> str:
        try:
            response = self._client.messages.create(
                model=self._current_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": message}],
            )
            return response.content[0].text
        except Exception as e:
            print(f"!!! Error generating response: {str(e)}")
            raise

    def get_providers(self) -> Dict[str, "LLMProvider"]:
        return {"anthropic": self}
