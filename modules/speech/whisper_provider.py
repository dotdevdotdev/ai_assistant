from core.interfaces.speech import SpeechToTextProvider
import whisper
import numpy as np
import io
import wave


class WhisperProvider(SpeechToTextProvider):
    def __init__(self):
        # Load the model - using base model for faster testing
        self.model = whisper.load_model("base")
        print(">>> Whisper model loaded")

    def transcribe(self, audio_frames):
        """Transcribe audio frames using Whisper"""
        try:
            print("\n=== Starting Whisper transcription ===")

            # Convert audio frames to WAV format in memory
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)  # 16-bit audio
                wf.setframerate(44100)  # Standard sample rate
                wf.writeframes(b"".join(audio_frames))

            # Convert to numpy array for Whisper
            wav_buffer.seek(0)
            with wave.open(wav_buffer, "rb") as wf:
                audio_data = np.frombuffer(
                    wf.readframes(wf.getnframes()), dtype=np.int16
                )
                # Convert to float32 and normalize
                audio_data = audio_data.astype(np.float32) / 32768.0

            print(f">>> Processing {len(audio_data)} samples")

            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_data,
                language="en",  # Can be made configurable
                fp16=False,  # Use fp32 for CPU
            )

            transcribed_text = result["text"].strip()
            print(f">>> Transcription complete: '{transcribed_text}'")

            return transcribed_text

        except Exception as e:
            print(f"!!! Error in Whisper transcription: {e}")
            return None
