from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QPushButton,
    QLabel,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
)
from PyQt6.QtCore import pyqtSignal, QTimer
from core.interfaces.assistant import AssistantProvider
from utils.registry import ProviderRegistry
import asyncio


class ModelConfigDialog(QDialog):
    def __init__(self, model_config: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Configuration")
        self.config = model_config
        self.values = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QFormLayout(self)

        for param, config in self.config.items():
            if config["type"] == "float":
                spinner = QDoubleSpinBox()
                spinner.setRange(config["min"], config["max"])
                spinner.setValue(config["default"])
                spinner.setSingleStep(0.1)
                self.values[param] = spinner
                layout.addRow(param.replace("_", " ").title(), spinner)

        buttons = QHBoxLayout()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)

        buttons.addWidget(ok_button)
        buttons.addWidget(cancel_button)
        layout.addRow("", buttons)

    def get_values(self) -> dict:
        return {k: v.value() for k, v in self.values.items()}


class AssistantSelector(QWidget):
    model_changed = pyqtSignal(str, dict)  # model_name, config

    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider = ProviderRegistry.get_instance().get_provider(AssistantProvider)
        self._current_config = {}
        self.setup_ui()
        # Use QTimer to call _load_models after initialization
        QTimer.singleShot(0, self._init_models)

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self._on_model_changed)

        self.config_button = QPushButton("⚙️")
        self.config_button.clicked.connect(self._show_config_dialog)
        self.config_button.setFixedWidth(40)

        layout.addWidget(QLabel("Model:"))
        layout.addWidget(self.model_combo, stretch=1)
        layout.addWidget(self.config_button)

    def _init_models(self):
        """Initialize models using the event loop"""
        asyncio.get_event_loop().create_task(self._load_models())

    async def _load_models(self):
        try:
            print("Loading available models...")
            # For Anthropic, we can hardcode the available models since they're fixed
            models = ["claude-3-opus-20240229", "claude-3-sonnet-20240229"]
            print(f"Available models: {models}")

            # Update UI in the main thread
            for model in models:
                self.model_combo.addItem(str(model))

        except Exception as e:
            print(f"Error loading models: {e}")
            # Add a default model if loading fails
            self.model_combo.addItem("claude-3-opus-20240229")

    def _on_model_changed(self, model_name: str):
        if model_name:
            try:
                # Use QTimer to handle the async operation
                QTimer.singleShot(0, lambda: self._update_model_config(model_name))
            except Exception as e:
                print(f"Error loading model config: {e}")

    def _update_model_config(self, model_name: str):
        """Helper method to update model config asynchronously"""

        async def _update():
            try:
                self._current_config = await self._provider.get_model_config(model_name)
                self.model_changed.emit(model_name, self._current_config)
            except Exception as e:
                print(f"Error updating model config: {e}")

        asyncio.get_event_loop().create_task(_update())

    def _show_config_dialog(self):
        if not self._current_config:
            return

        dialog = ModelConfigDialog(self._current_config, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            model_name = self.model_combo.currentText()
            config = dialog.get_values()
            self.model_changed.emit(model_name, config)
