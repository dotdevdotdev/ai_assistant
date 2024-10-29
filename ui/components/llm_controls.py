from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
    QApplication,
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
        """Send message to current model and emit response"""
        try:
            print(f"\n=== Sending message to model ===")
            provider = ProviderRegistry.get_instance().get_provider(LLMProvider)

            # Get system prompt and assistant info if selected
            window = self.window()
            system_prompt = None
            assistant_name = None
            if hasattr(window, "assistant_controls"):
                current_assistant = window.assistant_controls.get_current_assistant()
                if current_assistant:
                    system_prompt = current_assistant.system_prompt
                    assistant_name = current_assistant.name
                    print(f">>> Using assistant: {assistant_name}")
                    print(f">>> Using system prompt: {system_prompt[:100]}...")
                else:
                    system_prompt = self._app.config.llm.default_system_prompt
                    print(f">>> Using default system prompt: {system_prompt}")

            response = provider.generate_response(message, system_prompt=system_prompt)

            # Format response with assistant name if available
            formatted_response = (
                f"{assistant_name}: {response}" if assistant_name else response
            )
            self.response_ready.emit(formatted_response)

        except Exception as e:
            print(f"!!! Error generating response: {str(e)}")
            self.response_ready.emit(f"Error: {str(e)}")
            import traceback

            traceback.print_exc()
