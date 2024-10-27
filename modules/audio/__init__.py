from enum import Enum
from core.interfaces.audio import AudioInputProvider, AudioOutputProvider
from .pyaudio_provider import PyAudioProvider
from .sounddevice_provider import SoundDeviceProvider


class AudioProviderType(Enum):
    PYAUDIO = "pyaudio"
    SOUNDDEVICE = "sounddevice"


def create_audio_provider(provider_type: str) -> AudioInputProvider:
    providers = {
        "pyaudio": PyAudioProvider,
        "sounddevice": SoundDeviceProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown audio provider type: {provider_type}")

    return providers[provider_type]()
