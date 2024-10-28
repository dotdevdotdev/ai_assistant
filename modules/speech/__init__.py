from enum import Enum
from typing import Dict, Any, Union
from core.interfaces.speech import SpeechToTextProvider, TextToSpeechProvider
from .whisper_provider import WhisperProvider
from .deepgram_provider import DeepgramProvider
from .f5_provider import F5TTSProvider


class SpeechProviderType(Enum):
    WHISPER = "whisper"
    DEEPGRAM = "deepgram"
    F5TTS = "f5tts"
    ELEVENLABS = "elevenlabs"  # Add other TTS providers


def create_speech_provider(
    provider_type: str, config: Dict[str, Any] = None
) -> Union[SpeechToTextProvider, TextToSpeechProvider]:
    """Create and configure a speech provider"""
    providers = {
        "whisper": WhisperProvider,
        "deepgram": DeepgramProvider,
        "f5tts": F5TTSProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown speech provider type: {provider_type}")

    provider = providers[provider_type]()

    # Configure the provider if it has a configure method
    if hasattr(provider, "configure") and config:
        provider.configure(config)

    return provider
