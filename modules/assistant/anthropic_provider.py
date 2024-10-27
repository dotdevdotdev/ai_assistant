import os
from typing import AsyncIterator, Dict, Any, Optional
from anthropic import AsyncAnthropic
from core.interfaces.assistant import AssistantProvider, Message
from core.events import EventBus, Event, EventType


class AnthropicProvider(AssistantProvider):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided")

        self.client = AsyncAnthropic(api_key=self.api_key)
        self._event_bus = EventBus.get_instance()
        self._available_models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]

    async def send_message(
        self, messages: list[Message], **kwargs
    ) -> AsyncIterator[str]:
        try:
            model = kwargs.get("model", "claude-3-opus-20240229")
            temperature = kwargs.get("temperature", 0.7)

            # Convert messages to Anthropic format
            system_message = next(
                (msg.content for msg in messages if msg.role == "system"), None
            )

            conversation = []
            for msg in messages:
                if msg.role != "system":
                    conversation.append(
                        {
                            "role": "assistant" if msg.role == "assistant" else "user",
                            "content": msg.content,
                        }
                    )

            response = await self.client.messages.create(
                model=model,
                messages=conversation,
                system=system_message,
                temperature=temperature,
                stream=True,
            )

            async for chunk in response:
                if chunk.delta.text:
                    yield chunk.delta.text

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    def get_available_models(self) -> list[str]:
        return self._available_models.copy()

    async def get_model_config(self, model_name: str) -> Dict[str, Any]:
        return {
            "temperature": {"type": "float", "min": 0.0, "max": 1.0, "default": 0.7},
            "max_tokens": {"type": "int", "min": 1, "max": 4096, "default": 1024},
            "top_p": {"type": "float", "min": 0.0, "max": 1.0, "default": 1.0},
        }
