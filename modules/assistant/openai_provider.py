import os
from typing import AsyncIterator, Dict, Any, Optional
from openai import AsyncOpenAI
from core.interfaces.assistant import AssistantProvider, Message
from core.events import EventBus, Event, EventType


class OpenAIProvider(AssistantProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self._event_bus = EventBus.get_instance()
        self._available_models = None

    async def send_message(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[str]:
        try:
            model = kwargs.get("model", "gpt-4")
            temperature = kwargs.get("temperature", 0.7)

            formatted_messages = [
                {"role": msg.role, "content": msg.content} for msg in messages
            ]

            response = await self.client.chat.completions.create(
                model=model,
                messages=formatted_messages,
                temperature=temperature,
                stream=True,
            )

            async for chunk in response:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    async def get_available_models(self) -> list[str]:
        if self._available_models is None:
            try:
                models = await self.client.models.list()
                self._available_models = [
                    model.id
                    for model in models
                    if model.id.startswith(("gpt-4", "gpt-3.5"))
                ]
            except Exception as e:
                await self._event_bus.emit(Event(EventType.ERROR, error=e))
                raise
        return self._available_models

    async def get_model_config(self, model_name: str) -> Dict[str, Any]:
        base_config = {
            "temperature": {"type": "float", "min": 0.0, "max": 2.0, "default": 0.7},
            "max_tokens": {"type": "int", "min": 1, "max": 4096, "default": 1024},
        }

        if model_name.startswith("gpt-4"):
            base_config["max_tokens"]["max"] = 8192

        return base_config
