from abc import ABC, abstractmethod


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(self, audio_data):
        pass


class TextToSpeechProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> bytes:
        pass
