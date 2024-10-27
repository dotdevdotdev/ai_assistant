from enum import Enum
from typing import Dict, Any
from core.interfaces.speech import SpeechToTextProvider
from .whisper_provider import WhisperProvider
from .deepgram_provider import DeepgramProvider


class SpeechProviderType(Enum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"


def create_speech_provider(
    provider_type: str, config: Dict[str, Any] = None
) -> SpeechToTextProvider:
    """Create and configure a speech provider"""
    providers = {
        "whisper": WhisperProvider,
        "deepgram": DeepgramProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown speech provider type: {provider_type}")

    provider = providers[provider_type]()

    # Configure the provider if it has a configure method
    if hasattr(provider, "configure") and config:
        provider.configure(config)

    return provider
