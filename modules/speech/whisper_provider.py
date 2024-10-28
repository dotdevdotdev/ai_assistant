from core.interfaces.speech import SpeechToTextProvider
import whisper
import numpy as np
import io
import wave
import torch


class WhisperProvider(SpeechToTextProvider):
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("base.en", device=device)
        print(f">>> Whisper model loaded on {device}")

    def transcribe(self, audio_frames):
        try:
            print("\n=== Starting Whisper transcription ===")

            # Debug audio data
            print(f">>> Received {len(audio_frames)} audio frames")

            # Convert audio frames to numpy array directly
            audio_data = np.frombuffer(b"".join(audio_frames), dtype=np.int16)
            print(f">>> Audio data shape: {audio_data.shape}")
            print(f">>> Audio max value: {np.max(np.abs(audio_data))}")

            # Convert to float32 and normalize
            audio_float = audio_data.astype(np.float32) / 32768.0

            # Resample to 16kHz
            from scipy import signal

            original_rate = 44100
            target_rate = 16000
            samples = len(audio_float)
            new_samples = int(samples * target_rate / original_rate)
            audio_resampled = signal.resample(audio_float, new_samples)

            print(f">>> Resampled audio shape: {audio_resampled.shape}")
            print(f">>> Resampled max value: {np.max(np.abs(audio_resampled))}")

            # Transcribe using Whisper
            result = self.model.transcribe(
                audio_resampled,
                language="en",
                task="transcribe",
                fp16=False,
                temperature=0.0,
                best_of=1,
                beam_size=1,
                no_speech_threshold=0.3,
            )

            transcribed_text = result["text"].strip()
            print(f">>> Transcription complete: '{transcribed_text}'")

            return transcribed_text

        except Exception as e:
            print(f"!!! Error in Whisper transcription: {e}")
            return None
