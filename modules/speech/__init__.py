from enum import Enum, auto
from typing import Optional
from .whisper_provider import WhisperProvider
from .f5_provider import F5TTSProvider
from .elevenlabs_provider import ElevenLabsProvider


class SpeechProviderType(Enum):
    WHISPER = "whisper"
    F5TTS = "f5tts"
    ELEVENLABS = "elevenlabs"  # Add this


def create_speech_provider(provider_type: str, config: Optional[dict] = None):
    """Create a speech provider instance

    Args:
        provider_type: Type of provider to create
        config: Optional provider configuration

    Returns:
        Provider instance
    """
    try:
        provider_type = SpeechProviderType(provider_type.lower())
    except ValueError:
        raise ValueError(f"Unknown speech provider type: {provider_type}")

    if provider_type == SpeechProviderType.WHISPER:
        return WhisperProvider()
    elif provider_type == SpeechProviderType.F5TTS:
        return F5TTSProvider(config)
    elif provider_type == SpeechProviderType.ELEVENLABS:  # Add this
        return ElevenLabsProvider(config)
    else:
        raise ValueError(f"Unsupported speech provider type: {provider_type}")
