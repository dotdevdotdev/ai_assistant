from enum import Enum
from core.interfaces.assistant import AssistantProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider


class AssistantProviderType(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


def create_assistant_provider(provider_type: str) -> AssistantProvider:
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown assistant provider type: {provider_type}")

    return providers[provider_type]()
