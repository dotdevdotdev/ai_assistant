from core.interfaces.llm import LLMProvider
from openai import OpenAI
import os
from typing import Dict, Optional


class OpenAIProvider(LLMProvider):
    def __init__(self, config):
        self._config = config
        self._client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._current_model = self.get_default_model()

    def get_available_models(self):
        return self._config.models

    def get_default_model(self):
        return self._config.default_model

    def set_model(self, model_name: str):
        if model_name not in self.get_available_models():
            raise ValueError(f"Unknown model: {model_name}")
        self._current_model = model_name

    def generate_response(
        self, message: str, system_prompt: Optional[str] = None
    ) -> str:
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": message})

            response = self._client.chat.completions.create(
                model=self._current_model, messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"!!! Error generating response: {str(e)}")
            raise

    def get_providers(self) -> Dict[str, "LLMProvider"]:
        return {"openai": self}
