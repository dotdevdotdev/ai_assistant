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

            # Speech provider - ensure we pass the correct provider-specific config
            speech_provider_type = self.config.speech.provider_type
            speech_config = self.config.speech.config
            print(f"Speech provider type: {speech_provider_type}")
            print(f"Speech config: {speech_config}")

            speech_provider = create_speech_provider(
                speech_provider_type, speech_config
            )
            self.registry.register_provider(
                SpeechToTextProvider, speech_provider, speech_config
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

            # Add TTS provider
            print("\n=== Setting up TTS provider ===")
            tts_config = self.config.speech.config.get("f5tts", {})
            print(f">>> TTS config: {tts_config}")
            tts_provider = F5TTSProvider(model_name=tts_config.get("model", "F5-TTS"))
            self.registry.register_provider(TextToSpeechProvider, tts_provider)
            print(">>> TTS provider registered")

            # Register Whisper as the speech-to-text provider
            whisper_provider = WhisperProvider()
            self.registry.register_provider(SpeechToTextProvider, whisper_provider)

        except Exception as error:  # Changed from 'e' to 'error'
            print(f"Error in _setup_providers: {error}")  # Debug print
            self.loop.call_soon(
                lambda error=error: self.loop.create_task(  # Capture error in lambda
                    self.event_bus.emit(Event(EventType.ERROR, error=error))
                )
            )
            raise

    def _setup_style(self):
        """Apply application styling"""
        theme = AppTheme(dark_mode=True)  # TODO: Get from config
        self.app.setPalette(theme.get_palette())
        self.app.setStyleSheet(theme.get_stylesheet())

    def run(self):
        """Start the application"""
        try:
            self._setup_providers()
            self._setup_style()

            # Create and show main window with reference to application
            self.main_window = ChatWindow()
            self.main_window.app = self  # Give window access to application instance
            self.main_window.show()

            # Start the event loop
            return self.loop.run_forever()

        except Exception as e:
            print(f"Failed to start application: {e}", file=sys.stderr)
            return 1
