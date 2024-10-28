from abc import ABC, abstractmethod
from typing import Optional, BinaryIO, Callable
from dataclasses import dataclass


@dataclass
class AudioConfig:
    sample_rate: int
    channels: int
    chunk_size: int
    device_id: Optional[int] = None


class AudioInputProvider(ABC):
    @abstractmethod
    def start_recording(self, callback: Callable[[bytes], None]) -> None:
        """Start recording audio and call the callback with each chunk of audio data"""
        pass

    @abstractmethod
    def stop_recording(self) -> None:
        """Stop recording audio"""
        pass

    @abstractmethod
    def save_recording(self, filename: str) -> None:
        """Save the recorded audio to a file"""
        pass

    @abstractmethod
    def play_audio(self, audio_data) -> None:
        """Play audio data"""
        pass

    @abstractmethod
    def get_devices(self) -> list[dict]:
        """Get available audio input devices"""
        pass


class AudioOutputProvider(ABC):
    @abstractmethod
    def play_audio(self, audio_data: BinaryIO) -> None:
        """Play audio from data"""
        pass

    @abstractmethod
    def stop_playback(self) -> None:
        """Stop current audio playback"""
        pass
