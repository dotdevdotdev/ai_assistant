from abc import ABC, abstractmethod


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_data):
        pass


class TextToSpeechProvider(ABC):
    @abstractmethod
    async def synthesize(self, text: str, ref_audio: str = None) -> bytes:
        """Synthesize speech from text

        Args:
            text: Text to synthesize
            ref_audio: Optional reference audio file path (provider-specific)

        Returns:
            bytes: Audio data in WAV format
        """
        pass
