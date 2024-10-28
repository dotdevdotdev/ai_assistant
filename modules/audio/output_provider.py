import sounddevice as sd
import numpy as np
from typing import Optional
from core.interfaces import AudioOutputProvider


class SoundDeviceOutputProvider(AudioOutputProvider):
    def __init__(self, config: dict):
        self.device = config.get("output_device", None)
        self.sample_rate = config.get("sample_rate", 44100)

    def play_audio(self, audio_data: bytes, sample_rate: Optional[int] = None) -> None:
        # Convert bytes to numpy array
        audio_array = np.frombuffer(audio_data, dtype=np.float32)

        # Use provided sample rate or default
        sr = sample_rate or self.sample_rate

        # Play audio
        sd.play(audio_array, sr)
        sd.wait()  # Wait until audio is finished playing
