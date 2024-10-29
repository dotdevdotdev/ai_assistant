from core.interfaces.llm import LLMProvider
from anthropic import Anthropic
import os
import traceback
from dataclasses import dataclass
from typing import List


@dataclass
class LLMProviderConfig:
    default_model: str
    models: List[str]


class AnthropicProvider(LLMProvider):
    def __init__(self, config: LLMProviderConfig = None):
        self._client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._current_model = (
            config.default_model if config else "claude-3-haiku-20240307"
        )
        print(f">>> Initialized Anthropic provider with model: {self._current_model}")

    def generate_response(self, message: str, system_prompt: str = None) -> str:
        """Generate a response using the Anthropic API"""
        try:
            print(f"\n=== Generating response with {self._current_model} ===")

            # Build the messages list
            messages = []

            # Add system prompt if provided
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})

            # Add user message
            messages.append({"role": "user", "content": message})

            # Make the API call
            response = self._client.messages.create(
                model=self._current_model,
                messages=messages,
                max_tokens=1024,
                temperature=0.7,
            )

            # Extract and return the response content
            if response.content:
                return response.content[0].text
            return ""

        except Exception as e:
            print(f"!!! Error generating response: {e}")
            print(traceback.format_exc())
            raise

    def get_available_models(self) -> list:
        """Get list of available models"""
        return [
            "claude-3-opus-latest",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-latest",
        ]

    def get_default_model(self) -> str:
        """Get the default model name"""
        return self._current_model

    def set_model(self, model: str) -> None:
        """Set the current model"""
        if model in self.get_available_models():
            print(f">>> Switching to model: {model}")
            self._current_model = model
        else:
            raise ValueError(f"Unknown model: {model}")

    def get_providers(self) -> dict:
        return {"anthropic": self}
