import subprocess
import os
import asyncio
from core.interfaces.speech import TextToSpeechProvider
from core.events import EventBus, Event, EventType


class F5TTSProvider(TextToSpeechProvider):
    def __init__(self, model_name: str = "F5-TTS"):
        self._model = model_name
        self._event_bus = EventBus.get_instance()
        self._recordings_dir = "recordings"

    async def synthesize(self, text: str, ref_audio: str = None) -> bytes:
        """Convert text to speech using F5-TTS"""
        try:
            # Use latest recording as reference if none provided
            if not ref_audio:
                recordings = sorted(os.listdir(self._recordings_dir))
                if recordings:
                    ref_audio = os.path.join(self._recordings_dir, recordings[-1])
                else:
                    raise ValueError("No reference audio recordings found")

            # Prepare output path
            output_path = os.path.join(self._recordings_dir, "f5_tts_output.wav")

            # Build command
            cmd = [
                "f5-tts_infer-cli",
                "--model",
                self._model,
                "--ref_audio",
                ref_audio,
                "--ref_text",
                "",  # Let ASR transcribe
                "--gen_text",
                text,
                "--output",
                output_path,
            ]

            # Run F5-TTS
            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                raise RuntimeError(f"F5-TTS failed: {stderr.decode()}")

            # Read and return the generated audio
            with open(output_path, "rb") as f:
                return f.read()

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
