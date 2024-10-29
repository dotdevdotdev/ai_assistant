import subprocess
import os
import shutil
from typing import Optional
import pipes  # For proper shell escaping


class F5TTSProvider:
    def __init__(self, config: dict = None, **kwargs):
        """Initialize F5TTS provider

        Args:
            config: Dictionary that may contain:
                - model: Name of F5-TTS model to use
                - reference_audio_dir: Directory containing reference audio files
            **kwargs: Legacy support for direct parameters
        """
        if config is None:
            config = {}

        # Support legacy model_name parameter
        if "model_name" in kwargs:
            config["model"] = kwargs["model_name"]

        self._config = config

        # Support both 'model' and 'model_name' for backwards compatibility
        self._model = (
            self._config.get("model") or self._config.get("model_name") or "F5-TTS"
        )

        self._ref_audio_dir = self._config.get("reference_audio_dir", "reference_audio")
        self._output_dir = "resources/audio/f5tts"
        os.makedirs(self._output_dir, exist_ok=True)

    async def synthesize(self, text: str, ref_audio: Optional[str] = None) -> bytes:
        """Synthesize speech from text using F5-TTS"""
        try:
            if not ref_audio and os.path.exists(self._ref_audio_dir):
                # Use first wav file in reference directory
                wav_files = [
                    f for f in os.listdir(self._ref_audio_dir) if f.endswith(".wav")
                ]
                if wav_files:
                    ref_audio = os.path.join(self._ref_audio_dir, wav_files[0])
                    print(f">>> Using reference audio: {ref_audio}")

            # Remove existing output file
            output_file = os.path.join(self._output_dir, "infer_cli_out.wav")
            if os.path.exists(output_file):
                print(">>> Removing existing output file")
                os.remove(output_file)

            print("\n=== Generating speech with F5-TTS ===")
            print(f">>> Model: {self._model}")
            print(f">>> Reference audio: {ref_audio}")
            print(f">>> Text: {text}")
            print(f">>> Output dir: {self._output_dir}")

            # Properly escape the text and ref_audio path for shell
            escaped_text = pipes.quote(text)
            escaped_ref_audio = pipes.quote(ref_audio) if ref_audio else ""

            # Build command with properly escaped arguments
            cmd = f"f5-tts_infer-cli --model {self._model}"
            if ref_audio:
                cmd += f" --ref_audio {escaped_ref_audio}"
            cmd += f' --ref_text "" --gen_text {escaped_text} --output "{self._output_dir}"'

            print(f">>> Executing command: {cmd}")

            # Execute F5-TTS
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

            # Check if output file exists
            print(f">>> Checking for output file at: {output_file}")
            if not os.path.exists(output_file):
                raise FileNotFoundError(
                    f"F5-TTS did not create output file at {output_file}"
                )

            # Read the audio data
            with open(output_file, "rb") as f:
                audio_data = f.read()
            print(f">>> Successfully read {len(audio_data)} bytes of audio data")

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
