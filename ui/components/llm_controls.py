from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QApplication,
    QTextEdit,
)
from PyQt6.QtCore import pyqtSignal, QTimer
from core.interfaces.llm import LLMProvider
from utils.registry import ProviderRegistry


class LLMControls(QWidget):
    model_changed = pyqtSignal(str)  # Emits model name when changed
    response_ready = pyqtSignal(str)  # Emits response text

    def __init__(self, parent=None):
        super().__init__(parent)
        print("\n=== Initializing LLM Controls ===")
        self._setup_ui()
        # Delay model loading until window is fully initialized
        QTimer.singleShot(0, self._initialize_models)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Model selection
        model_layout = QHBoxLayout()
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_layout.addWidget(QLabel("LLM Model:"))
        model_layout.addWidget(self.model_combo, stretch=1)
        layout.addLayout(model_layout)

        # System prompt
        self.system_prompt_edit = QTextEdit()
        self.system_prompt_edit.setPlaceholderText("Enter system prompt (optional)...")
        self.system_prompt_edit.setMaximumHeight(100)
        layout.addWidget(self.system_prompt_edit)

    def _initialize_models(self):
        """Initialize models after window is fully set up"""
        print("\n=== Initializing LLM Models ===")
        window = self.window()
        if hasattr(window, "app"):
            print(">>> Found application instance")
            self._app = window.app
            self._load_models()
        else:
            print("!!! Window not fully initialized, retrying in 100ms")
            QTimer.singleShot(100, self._initialize_models)

    def _load_models(self):
        """Load available models from all providers"""
        try:
            print("\n=== Loading LLM Models ===")
            self.model_combo.clear()

            providers = self._app._llm_providers
            print(f"Available providers: {list(providers.keys())}")

            for provider_name, provider in providers.items():
                print(f"Loading models for {provider_name}")
                for model in provider.get_available_models():
                    display_name = f"{provider_name}: {model}"
                    print(f"Adding model: {display_name}")
                    self.model_combo.addItem(display_name)

            # Set default model from first provider
            if providers:
                first_provider = next(iter(providers.values()))
                default_model = first_provider.get_default_model()
                default_provider = next(iter(providers.keys()))
                default_display = f"{default_provider}: {default_model}"
                index = self.model_combo.findText(default_display)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
                    print(f"Set default model to: {default_display}")

        except Exception as e:
            print(f"!!! Error loading models: {str(e)}")
            import traceback

            traceback.print_exc()

    def _on_model_changed(self, display_name: str):
        """Handle model selection change"""
        try:
            if not display_name:  # Skip empty selections
                return

            print(f"\n=== Model changed to: {display_name} ===")
            provider_name, model_name = display_name.split(": ", 1)

            # Get the provider from application
            provider = self._app._llm_providers[provider_name]

            # Update the registry with the selected provider
            ProviderRegistry.get_instance().register_provider(LLMProvider, provider)

            # Set the model
            provider.set_model(model_name)
            self.model_changed.emit(model_name)

            print(f"Switched to provider {provider_name} with model {model_name}")

        except Exception as e:
            print(f"!!! Error changing model: {str(e)}")
            import traceback

            traceback.print_exc()

    def send_message(self, message: str):
        """Send message to LLM and emit response"""
        try:
            # Get current provider and settings
            provider = self._get_current_provider()
            if not provider:
                error_msg = "No LLM provider available"
                print(f"!!! {error_msg}")
                self.response_ready.emit(error_msg)
                return

            system_prompt = self.system_prompt_edit.toPlainText().strip()

            # Validate message
            if not message.strip():
                error_msg = "Message cannot be empty"
                print(f"!!! {error_msg}")
                self.response_ready.emit(error_msg)
                return

            try:
                response = provider.generate_response(
                    message, system_prompt=system_prompt
                )
                if response and response.strip():
                    self.response_ready.emit(response)
                else:
                    error_msg = "Received empty response from LLM"
                    print(f"!!! {error_msg}")
                    self.response_ready.emit(error_msg)
            except Exception as e:
                error_msg = f"Error generating response: {str(e)}"
                print(f"!!! {error_msg}")
                self.response_ready.emit(error_msg)

        except Exception as e:
            error_msg = f"Error in message handling: {str(e)}"
            print(f"!!! {error_msg}")
            self.response_ready.emit(error_msg)

    def _get_current_provider(self) -> LLMProvider:
        """Get the currently selected LLM provider"""
        try:
            # Get the current model selection
            display_name = self.model_combo.currentText()
            if not display_name:
                print("!!! No model selected")
                return None

            # Split into provider and model names
            provider_name, _ = display_name.split(": ", 1)

            # Get provider from application
            if provider_name in self._app._llm_providers:
                return self._app._llm_providers[provider_name]
            else:
                print(f"!!! Provider {provider_name} not found")
                return None

        except Exception as e:
            print(f"!!! Error getting current provider: {e}")
            return None
