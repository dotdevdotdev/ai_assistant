import sys
import os
import asyncio
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from config.settings import AppConfig
from utils.registry import ProviderRegistry
from core.events import EventBus, EventType, Event
from ui.chat_window import ChatWindow
from ui.styles import AppTheme
from modules.audio import create_audio_provider
from modules.speech import create_speech_provider, F5TTSProvider, WhisperProvider
from modules.assistant import create_assistant_provider
from modules.clipboard import create_clipboard_provider
from core.interfaces.audio import AudioInputProvider
from core.interfaces.speech import SpeechToTextProvider, TextToSpeechProvider
from core.interfaces.assistant import AssistantProvider
from core.interfaces.clipboard import ClipboardProvider
from qasync import QEventLoop
from modules.llm.anthropic_provider import AnthropicProvider
from core.interfaces.llm import LLMProvider
from modules.llm.openai_provider import OpenAIProvider
from modules.llm.composite_provider import CompositeLLMProvider
from modules.speech.elevenlabs_provider import ElevenLabsProvider
from modules.speech.composite_tts_provider import CompositeTTSProvider


class Application:
    CONFIG_PATH = os.path.join(os.path.dirname(__file__), "app-settings.yaml")

    def __init__(self):
        self.app = QApplication(sys.argv)
        self.event_bus = EventBus.get_instance()
        self.registry = ProviderRegistry.get_instance()

        # Set up asyncio integration with Qt
        self.loop = QEventLoop(self.app)
        asyncio.set_event_loop(self.loop)

        print(f"Loading config from: {os.path.abspath(self.CONFIG_PATH)}")
        self.config = AppConfig.load(self.CONFIG_PATH)
        self._setup_event_handling()

        # Register LLM providers
        llm_config = self.config.llm
        print("\n=== Setting up LLM Providers ===")

        # Create all configured providers
        providers = {}
        if "anthropic" in llm_config.providers:
            print(">>> Registering Anthropic provider")
            providers["anthropic"] = AnthropicProvider(
                llm_config.providers["anthropic"]
            )
        if "openai" in llm_config.providers:
            print(">>> Registering OpenAI provider")
            providers["openai"] = OpenAIProvider(llm_config.providers["openai"])

        if not providers:
            raise ValueError("No valid LLM providers configured")

        # Register the composite provider
        composite_provider = CompositeLLMProvider(providers)
        self.registry.register_provider(LLMProvider, composite_provider)

        # Store all providers for potential switching
        self._llm_providers = dict(providers)
        print(f">>> Available providers: {list(self._llm_providers.keys())}")

    def _setup_event_handling(self):
        self.event_bus.subscribe(EventType.ERROR, self._handle_error)

    async def _handle_error(self, event: Event):
        # TODO: Implement proper error handling/display
        print(f"Error occurred: {event.error}", file=sys.stderr)

    def _setup_providers(self):
        """Initialize and register all providers"""
        try:
            # Audio provider
            audio_config = self.config.audio.config.copy()

            # Get app-level settings if they exist
            app_settings = self.config.ui.get("app", {})
            if isinstance(app_settings, dict):
                print(f"Found app settings: {app_settings}")

                # Add input/output device settings from app config if they exist
                if "input_device" in app_settings:
                    audio_config["input_device"] = app_settings["input_device"]
                if "output_device" in app_settings:
                    audio_config["output_device"] = app_settings["output_device"]

            print(f"Final audio config: {audio_config}")

            audio_provider = create_audio_provider(self.config.audio.provider_type)
            self.registry.register_provider(
                AudioInputProvider, audio_provider, audio_config
            )

            # Speech providers setup
            print("\n=== Setting up Speech Providers ===")

            # Speech-to-Text (STT) providers
            print(">>> Setting up STT providers")
            stt_config = self.config.speech.stt.config.get(
                self.config.speech.stt.provider_type, {}
            )
            stt_provider = WhisperProvider()  # For now, just using Whisper
            self.registry.register_provider(SpeechToTextProvider, stt_provider)
            print(
                f">>> Registered STT provider: {self.config.speech.stt.provider_type}"
            )

            # Text-to-Speech (TTS) providers
            print("\n>>> Setting up TTS providers")
            tts_providers = {}

            # Register ElevenLabs provider
            print(">>> Setting up ElevenLabs TTS provider")
            elevenlabs_config = self.config.speech.tts.config.get("elevenlabs", {})
            tts_providers["elevenlabs"] = ElevenLabsProvider(elevenlabs_config)
            print(">>> ElevenLabs TTS provider registered")

            # Register F5TTS provider
            print(">>> Setting up F5TTS provider")
            f5tts_config = self.config.speech.tts.config.get("f5tts", {})
            provider_config = {
                "model": f5tts_config.get("model", "F5-TTS"),
                "reference_audio_dir": f5tts_config.get(
                    "reference_audio_dir", "reference_audio"
                ),
            }
            tts_providers["f5tts"] = F5TTSProvider(config=provider_config)
            print(">>> F5TTS provider registered")

            # Create and register the composite TTS provider
            active_provider = self.config.speech.tts.provider_type
            print(
                f">>> Setting up composite TTS with active provider: {active_provider}"
            )
            print(f">>> Available TTS providers: {list(tts_providers.keys())}")
            composite_tts = CompositeTTSProvider(tts_providers, active_provider)
            self.registry.register_provider(TextToSpeechProvider, composite_tts)
            print(
                f">>> Registered composite TTS provider with active provider: {active_provider}"
            )

            # Assistant provider
            assistant_provider = create_assistant_provider(
                self.config.assistant.provider_type
            )
            self.registry.register_provider(
                AssistantProvider, assistant_provider, self.config.assistant.config
            )

            # Clipboard provider
            clipboard_provider = create_clipboard_provider(
                self.config.clipboard.provider_type
            )
            self.registry.register_provider(ClipboardProvider, clipboard_provider)

        except Exception as error:
            print(f"Error in _setup_providers: {error}")
            self.loop.call_soon(
                lambda error=error: self.loop.create_task(
                    self.event_bus.emit(Event(EventType.ERROR, error=error))
                )
            )
            raise

    def _setup_style(self):
        """Apply application styling"""
        theme_colors = self.config.ui["theme"]["colors"]
        theme = AppTheme(colors=theme_colors)
        self.app.setPalette(theme.get_palette())
        self.app.setStyleSheet(theme.get_stylesheet())

    def run(self):
        """Start the application"""
        try:
            self._setup_providers()
            self._setup_style()

            # Create and show main window
            self.main_window = ChatWindow()
            self.main_window.set_app(self)  # Set app before UI setup
            self.main_window.show()

            # Start the event loop
            return self.loop.run_forever()

        except Exception as e:
            print(f"Failed to start application: {e}", file=sys.stderr)
            return 1
