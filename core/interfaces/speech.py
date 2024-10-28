from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional


class SpeechToTextProvider(ABC):
    @abstractmethod
    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        """Convert streaming audio to text"""
        pass

    @abstractmethod
    async def transcribe_file(self, audio_file: bytes) -> str:
        """Convert audio file to text"""
        pass


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, ref_audio: Optional[str] = None) -> bytes:
        """Convert text to speech, optionally using reference audio for voice cloning"""
        pass
