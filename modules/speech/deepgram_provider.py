from typing import AsyncIterator, Optional
import os
import asyncio
import numpy as np
from scipy import signal
from deepgram import DeepgramClient
from core.interfaces.speech import SpeechToTextProvider
import traceback
import io
import wave
import logging
from collections import deque
import gc


class DeepgramProvider(SpeechToTextProvider):
    def __init__(self, api_key: Optional[str] = None):
        print("\n=== Initializing Deepgram Provider ===")
        self.api_key = api_key or os.getenv("DEEPGRAM_API_KEY")
        if not self.api_key:
            raise ValueError("Deepgram API key not provided")

        self.client = DeepgramClient(self.api_key)
        self._running = False
        self._source_rate = None
        self._target_rate = 16000
        self._chunk_size = None
        self._channels = None
        self._max_buffer_size = 5  # Maximum number of chunks to store
        print(">>> Provider initialized")

    def configure(self, config: dict):
        """Configure provider with audio settings"""
        print(f"\n=== Configuring Deepgram with: {config} ===")
        self._source_rate = config.get("sample_rate", 48000)
        self._chunk_size = config.get("chunk_size", 2048)
        self._channels = config.get("channels", 1)
        print(f">>> Source sample rate: {self._source_rate}")
        print(f">>> Chunk size: {self._chunk_size}")
        print(f">>> Channels: {self._channels}")

    async def transcribe_stream(
        self, audio_stream: AsyncIterator[bytes]
    ) -> AsyncIterator[str]:
        print("\n=== Starting Deepgram transcription ===")
        if not self._source_rate:
            raise ValueError("Source sample rate not configured")

        try:
            self._running = True
            buffer = deque(maxlen=self._max_buffer_size)  # Use deque with max size
            total_samples = 0
            min_samples = int(self._source_rate * 0.5)  # Process every 0.5 seconds

            print(f">>> Buffer will process every {min_samples} samples")
            print(f">>> Max buffer size: {self._max_buffer_size} chunks")

            async for chunk in audio_stream:
                if not self._running:
                    break

                try:
                    if not chunk:
                        print("!!! Warning: Empty chunk received")
                        continue

                    # Convert bytes to float32 array
                    audio_float = np.frombuffer(
                        chunk, dtype=np.float32
                    ).copy()  # Make a copy
                    if len(audio_float) == 0:
                        print("!!! Warning: Empty audio data after conversion")
                        continue

                    # Normalize if needed
                    max_val = np.max(np.abs(audio_float))
                    if max_val > 1.0:
                        audio_float = audio_float / max_val

                    # Add to buffer
                    buffer.append(audio_float)
                    total_samples += len(audio_float)

                    # Process when we have enough samples
                    if total_samples >= min_samples:
                        try:
                            # Convert buffer to list and concatenate
                            audio_data = np.concatenate(list(buffer))

                            # Clear buffer references
                            buffer.clear()
                            gc.collect()  # Force garbage collection

                            # Resample to target rate
                            target_length = int(
                                len(audio_data) * self._target_rate / self._source_rate
                            )
                            resampled = signal.resample(audio_data, target_length)

                            # Clear original audio data
                            del audio_data
                            gc.collect()

                            # Convert to int16
                            audio_int16 = (resampled * 32767.0).astype(np.int16)
                            del resampled
                            gc.collect()

                            # Create WAV buffer
                            wav_buffer = io.BytesIO()
                            with wave.open(wav_buffer, "wb") as wav:
                                wav.setnchannels(1)
                                wav.setsampwidth(2)
                                wav.setframerate(self._target_rate)
                                wav.writeframes(audio_int16.tobytes())

                            del audio_int16
                            gc.collect()

                            # Reset position for reading
                            wav_buffer.seek(0)

                            # Send to Deepgram
                            response = await self.client.transcription.prerecorded.v(
                                "1"
                            ).transcribe(
                                {"buffer": wav_buffer.read(), "mimetype": "audio/wav"},
                                {
                                    "smart_format": True,
                                    "model": "nova-2",
                                    "language": "en",
                                    "punctuate": True,
                                },
                            )

                            # Extract transcription
                            transcript = response["results"]["channels"][0][
                                "alternatives"
                            ][0]["transcript"]

                            if transcript.strip():
                                yield transcript

                            # Reset counters
                            total_samples = 0
                            gc.collect()

                        except Exception as e:
                            print(f"!!! Error processing buffer: {e}")
                            print(traceback.format_exc())
                            buffer.clear()
                            total_samples = 0
                            gc.collect()

                except Exception as e:
                    print(f"!!! Error processing chunk: {e}")
                    print(traceback.format_exc())
                    buffer.clear()
                    total_samples = 0
                    gc.collect()

        except Exception as e:
            print(f"!!! Transcription error: {e}")
            print(traceback.format_exc())
        finally:
            self._running = False
            print(">>> Transcription ended")

    async def transcribe_file(self, audio_file: bytes) -> str:
        try:
            wav_buffer = io.BytesIO(audio_file)
            response = await self.client.transcription.prerecorded.v("1").transcribe(
                {"buffer": wav_buffer.read(), "mimetype": "audio/wav"},
                {
                    "smart_format": True,
                    "model": "nova-2",
                    "language": "en",
                },
            )
            return response["results"]["channels"][0]["alternatives"][0]["transcript"]
        except Exception as e:
            print(f"!!! File transcription error: {e}")
            print(traceback.format_exc())
            raise

    def __del__(self):
        self._running = False
