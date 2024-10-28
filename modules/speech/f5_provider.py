import os
import subprocess
import logging
import io
from pathlib import Path
from core.interfaces.speech import TextToSpeechProvider
import wave


class F5TTSProvider(TextToSpeechProvider):
    def __init__(self, model_name: str = "F5-TTS"):
        self.model_name = model_name
        # Create fixed output directory in project root
        self.output_dir = Path("resources/audio/f5tts")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "f5tts_output.wav"

    async def synthesize(self, text: str, ref_audio: str) -> bytes:
        """Generate speech using F5-TTS"""
        try:
            print(f"\n=== Generating speech with F5-TTS ===")
            print(f">>> Model: {self.model_name}")
            print(f">>> Reference audio: {ref_audio}")
            print(f">>> Text: {text}")
            print(f">>> Output dir: {self.output_dir}")

            # Clean up any existing output file
            actual_output = self.output_dir / "infer_cli_out.wav"
            if actual_output.exists():
                print(">>> Removing existing output file")
                actual_output.unlink()

            # Ensure text is properly quoted for shell
            text = f'"{text}"'  # Add quotes around text
            ref_text = '""'  # Empty quoted string for ref text

            # Build command as a single string
            cmd = f'f5-tts_infer-cli --model {self.model_name} --ref_audio "{ref_audio}" --ref_text {ref_text} --gen_text {text} --output "{self.output_dir}"'

            print(f">>> Executing command: {cmd}")

            # Use shell=True to handle the quoting properly
            process = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            stdout, stderr = process.communicate()

            if stdout:
                print(f">>> F5-TTS stdout:\n{stdout}")
            if stderr:
                print(f">>> F5-TTS stderr:\n{stderr}")

            print(f">>> Process completed with return code: {process.returncode}")

            if process.returncode != 0:
                raise RuntimeError(
                    f"F5-TTS failed with code {process.returncode}: {stderr}"
                )

            print(f">>> Checking for output file at: {actual_output}")
            if not actual_output.exists():
                raise FileNotFoundError(
                    f"F5-TTS output file not found at {actual_output}"
                )

            # Get file size before reading
            file_size = actual_output.stat().st_size
            print(f">>> Output file size: {file_size} bytes")

            # Read the generated audio file
            with open(actual_output, "rb") as f:
                audio_data = f.read()

            print(f">>> Successfully read {len(audio_data)} bytes of audio data")

            # Verify the WAV file structure
            with wave.open(io.BytesIO(audio_data), "rb") as wf:
                print(f">>> WAV file details:")
                print(f"    Channels: {wf.getnchannels()}")
                print(f"    Sample width: {wf.getsampwidth()}")
                print(f"    Frame rate: {wf.getframerate()}")
                print(f"    Number of frames: {wf.getnframes()}")
                print(
                    f"    Duration: {wf.getnframes() / wf.getframerate():.2f} seconds"
                )

            return audio_data

        except Exception as e:
            print(f"!!! Error in F5-TTS synthesis: {e}")
            raise


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
