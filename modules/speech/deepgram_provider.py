from core.interfaces.speech import SpeechToTextProvider


class DeepgramProvider(SpeechToTextProvider):
    def transcribe(self, audio_data):
        # Implementation specific to Deepgram
        pass
