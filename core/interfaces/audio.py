from abc import ABC, abstractmethod
from typing import Optional, BinaryIO
from dataclasses import dataclass


@dataclass
class AudioConfig:
    sample_rate: int
    channels: int
    chunk_size: int
    device_id: Optional[int] = None


class AudioInputProvider(ABC):
    @abstractmethod
    def start_stream(self, config: AudioConfig) -> None:
        """Start audio input stream"""
        pass

    @abstractmethod
    def read_chunk(self) -> bytes:
        """Read a chunk of audio data"""
        pass

    @abstractmethod
    def stop_stream(self) -> None:
        """Stop audio input stream"""
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
