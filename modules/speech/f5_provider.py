import subprocess
import os
import asyncio
import shutil
import torch
from pathlib import Path
from core.interfaces.speech import TextToSpeechProvider
from core.events import EventBus, Event, EventType
import tempfile
import logging
from core.interfaces import TextToSpeechProvider, AudioInputProvider, AudioDeviceManager
from utils.registry import ProviderRegistry
import io


class F5TTSProvider(TextToSpeechProvider):
    def __init__(self, model_name: str = "F5-TTS"):
        self._model = model_name
        self._event_bus = EventBus.get_instance()
        self._recordings_dir = "recordings"
        self._f5_cli_path = self._find_f5_cli()
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        if self._device == "cpu":
            print("WARNING: Running F5-TTS on CPU - this will be slow!")

        # Create recordings directory if it doesn't exist
        Path(self._recordings_dir).mkdir(parents=True, exist_ok=True)

    def _find_f5_cli(self) -> str:
        """Find the F5-TTS CLI executable"""
        # Try common installation paths
        possible_paths = [
            shutil.which("f5-tts_infer-cli"),  # Check PATH
            "/usr/local/bin/f5-tts_infer-cli",
            os.path.expanduser("~/.local/bin/f5-tts_infer-cli"),
        ]

        for path in possible_paths:
            if path and os.path.isfile(path):
                return path

        installation_msg = """
F5-TTS CLI not found. Please install it using:
1. pip install f5-tts
2. Or install from source:
   git clone https://github.com/FreedomIntelligence/F5-TTS
   cd F5-TTS
   pip install -e .
"""
        raise RuntimeError(installation_msg)

    async def synthesize(self, text: str, ref_audio: str) -> bytes:
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                output_path = os.path.join(temp_dir, "output.wav")

                cmd = [
                    "f5-tts_infer-cli",
                    "--model",
                    "F5-TTS",
                    "--ref_audio",
                    ref_audio,
                    "--ref_text",
                    "",
                    "--gen_text",
                    text,
                    "--output",
                    output_path,
                ]

                logging.debug(f"Executing F5-TTS command: {' '.join(cmd)}")

                process = await asyncio.create_subprocess_exec(
                    *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
                )

                stdout, stderr = await process.communicate()

                if process.returncode != 0:
                    raise RuntimeError(
                        f"F5-TTS failed with code {process.returncode}: {stderr.decode()}"
                    )

                actual_output = os.path.join(output_path, "infer_cli_out.wav")
                logging.debug(f"Looking for output file at: {actual_output}")

                if not os.path.exists(actual_output):
                    raise FileNotFoundError(
                        f"F5-TTS did not generate output file at {actual_output}"
                    )

                # Read the file into a BytesIO object
                with open(actual_output, "rb") as f:
                    audio_data = f.read()

                # Use AudioDeviceManager instead
                audio_manager = ProviderRegistry.get_instance().get_provider(
                    AudioDeviceManager
                )
                audio_manager.play_audio(io.BytesIO(audio_data))

                return audio_data

        except Exception as e:
            raise RuntimeError(f"F5-TTS failed: {str(e)}")


# TODO: F5-TTS Provider Status
# - Basic provider structure is in place
# - CLI command execution is set up but not producing output
# - Need to verify:
#   1. F5-TTS model installation
#   2. CUDA/CPU compatibility
#   3. Audio format compatibility
#   4. Reference audio requirements
# - Consider adding:
#   1. Model download/verification
#   2. Voice profile management
#   3. Audio preprocessing for reference files
#   4. Progress callbacks during generation
