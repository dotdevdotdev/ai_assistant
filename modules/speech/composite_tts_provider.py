from core.interfaces.speech import TextToSpeechProvider
from typing import Dict, Optional


class CompositeTTSProvider(TextToSpeechProvider):
    def __init__(
        self, providers: Dict[str, TextToSpeechProvider], active_provider: str
    ):
        self._providers = providers
        self._active_provider = active_provider

    def set_active_provider(self, provider_name: str):
        """Change the active provider"""
        if provider_name not in self._providers:
            raise ValueError(f"Unknown provider: {provider_name}")
        print(f">>> Switching TTS provider to: {provider_name}")
        self._active_provider = provider_name

    def get_active_provider(self) -> str:
        """Get the name of the currently active provider"""
        return self._active_provider

    def get_available_providers(self) -> list[str]:
        """Get list of available provider names"""
        return list(self._providers.keys())

    async def synthesize(self, text: str, ref_audio: Optional[str] = None) -> bytes:
        """Synthesize speech using the active provider"""
        provider = self._providers.get(self._active_provider)
        if not provider:
            raise ValueError(f"No provider found for: {self._active_provider}")
        return await provider.synthesize(text, ref_audio)
