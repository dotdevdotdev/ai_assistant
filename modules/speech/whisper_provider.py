import whisper
from typing import AsyncIterator
import numpy as np
from core.interfaces.speech import SpeechToTextProvider
from core.events import EventBus, Event, EventType
from scipy import signal


class WhisperProvider(SpeechToTextProvider):
    def __init__(self, model_name: str = "base"):
        print(f"Initializing Whisper with model: {model_name}")
        self.model = whisper.load_model(model_name)
        self._event_bus = EventBus.get_instance()
        self._buffer = []  # Store chunks as list instead of bytearray
        self._target_sample_rate = 16000  # Whisper expects 16kHz
        self._source_sample_rate = None  # Will be set from first chunk

    def _resample_audio(
        self, audio_data: np.ndarray, orig_sr: int, target_sr: int
    ) -> np.ndarray:
        """Resample audio data to target sample rate"""
        if orig_sr == target_sr:
            return audio_data

        print(f"Resampling from {orig_sr}Hz to {target_sr}Hz")
        # Calculate resampling ratio
        ratio = target_sr / orig_sr
        target_length = int(len(audio_data) * ratio)

        # Resample using scipy's resample function
        resampled = signal.resample(audio_data, target_length)
        return resampled

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        print("\n=== Starting new transcription stream ===")
        try:
            async for chunk in audio_stream:
                print(f"\nReceived audio chunk: {len(chunk)} bytes")
                # Convert chunk to numpy array and store
                chunk_data = np.frombuffer(chunk, dtype=np.float32)
                print(f"Converted to numpy array: {len(chunk_data)} samples")
                print(
                    f"Audio range: min={np.min(chunk_data):.3f}, max={np.max(chunk_data):.3f}"
                )

                # Set source sample rate from first chunk if not set
                if self._source_sample_rate is None:
                    # Calculate based on chunk size and expected duration
                    chunk_duration = 0.093  # ~93ms for 4096 samples at 44.1kHz
                    self._source_sample_rate = int(len(chunk_data) / chunk_duration)
                    print(
                        f"\n>>> Detected source sample rate: {self._source_sample_rate}Hz"
                    )

                self._buffer.append(chunk_data)
                total_samples = sum(len(chunk) for chunk in self._buffer)
                print(
                    f"Buffer size: {total_samples} samples ({len(self._buffer)} chunks)"
                )

                # Process if we have enough audio (2 seconds at source rate)
                min_samples = int(self._source_sample_rate * 2)  # 2 seconds of audio
                if total_samples >= min_samples:
                    print(f"\n=== Processing buffer with {total_samples} samples ===")
                    # Concatenate all chunks
                    audio_data = np.concatenate(self._buffer)
                    print(f"Concatenated audio: {len(audio_data)} samples")

                    # Ensure audio is in [-1, 1] range
                    max_val = np.max(np.abs(audio_data))
                    if max_val > 1.0:
                        print(f"Normalizing audio from max value of {max_val}")
                        audio_data = audio_data / max_val
                        print(
                            f"After normalization: min={np.min(audio_data):.3f}, max={np.max(audio_data):.3f}"
                        )

                    # Resample to 16kHz for Whisper
                    audio_data = self._resample_audio(
                        audio_data, self._source_sample_rate, self._target_sample_rate
                    )
                    print(
                        f"After resampling: {len(audio_data)} samples at {self._target_sample_rate}Hz"
                    )

                    try:
                        print("\n>>> Sending to Whisper for transcription...")
                        result = self.model.transcribe(audio_data)
                        text = result["text"].strip()
                        if text:
                            print(f">>> Transcribed text: '{text}'")
                            yield text
                        else:
                            print(">>> No text transcribed from audio segment")
                    except Exception as e:
                        print(f"!!! Error during transcription: {e}")
                        continue

                    # Keep last 0.5 seconds for overlap
                    overlap_samples = int(self._source_sample_rate * 0.5)
                    last_chunk = np.concatenate(self._buffer)[-overlap_samples:]
                    self._buffer = [last_chunk]
                    print(f"Keeping {len(last_chunk)} samples for overlap")

        except Exception as e:
            print(f"!!! Error in transcribe_stream: {e}")
            raise

    async def transcribe_file(self, audio_file: bytes) -> str:
        try:
            audio_data = np.frombuffer(audio_file, dtype=np.float32)
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = np.clip(audio_data, -1.0, 1.0)

            # Resample if needed
            audio_data = self._resample_audio(
                audio_data, self._source_sample_rate, self._target_sample_rate
            )

            result = self.model.transcribe(audio_data)
            return result["text"]
        except Exception as e:
            print(f"Error in transcribe_file: {e}")
            raise
