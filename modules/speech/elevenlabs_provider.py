from core.interfaces.speech import TextToSpeechProvider
import requests
import os
import asyncio
import io
from pydub import AudioSegment


class ElevenLabsProvider(TextToSpeechProvider):
    API_BASE = "https://api.elevenlabs.io/v1"
    CHUNK_SIZE = 1024

    def __init__(self, config: dict = None):
        """Initialize ElevenLabs provider

        Args:
            config: Dictionary containing:
                - api_key: ElevenLabs API key
                - model_id: Model ID to use
                - voice_id: Voice ID to use
                - voice_settings: Dict of voice settings
        """
        if config is None:
            config = {}

        # Set API key from environment or config
        self._api_key = os.getenv("ELEVENLABS_API_KEY") or config.get("api_key")
        if not self._api_key:
            raise ValueError("ElevenLabs API key not found in environment or config")

        self._config = config
        self._model_id = config.get("model_id", "eleven_monolingual_v1")
        self._voice_id = config.get("voice_id")

        # Store voice settings
        voice_settings = config.get("voice_settings", {})
        self._voice_settings = {
            "stability": voice_settings.get("stability", 0.5),
            "similarity_boost": voice_settings.get("similarity_boost", 0.5),
            "style": voice_settings.get("style", 0.5),
            "use_speaker_boost": voice_settings.get("speaker_boost", True),
        }

    async def synthesize(self, text: str, ref_audio: str = None) -> bytes:
        """Synthesize speech using ElevenLabs API

        Note: ref_audio is ignored as ElevenLabs uses predefined voices
        """
        try:
            print(f">>> ElevenLabs synthesis with voice_id: {self._voice_id}")
            print(f">>> Model: {self._model_id}")
            print(f">>> Voice settings:")
            print(f"    Stability: {self._voice_settings['stability']}")
            print(f"    Similarity Boost: {self._voice_settings['similarity_boost']}")
            print(f"    Style: {self._voice_settings['style']}")
            print(f"    Speaker Boost: {self._voice_settings['use_speaker_boost']}")

            # Set up request
            url = f"{self.API_BASE}/text-to-speech/{self._voice_id}/stream"
            headers = {"Accept": "application/json", "xi-api-key": self._api_key}
            data = {
                "text": text,
                "model_id": self._model_id,
                "voice_settings": self._voice_settings,
            }

            # Make request in thread pool since it's blocking
            def make_request():
                response = requests.post(url, headers=headers, json=data, stream=True)
                if not response.ok:
                    raise RuntimeError(f"ElevenLabs API error: {response.text}")

                # Read all chunks into bytes
                audio_data = b""
                for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                    audio_data += chunk

                # Convert MP3 to WAV
                audio_segment = AudioSegment.from_mp3(io.BytesIO(audio_data))
                wav_buffer = io.BytesIO()
                audio_segment.export(wav_buffer, format="wav")
                return wav_buffer.getvalue()

            # Run in thread pool
            audio_data = await asyncio.get_event_loop().run_in_executor(
                None, make_request
            )

            print(">>> Successfully converted audio to WAV format")
            return audio_data

        except Exception as e:
            print(f"!!! Error in ElevenLabs synthesis: {e}")
            raise
