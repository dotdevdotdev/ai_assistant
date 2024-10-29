from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal
from typing import Optional
from config.settings import AssistantConfig


class AssistantControls(QWidget):
    assistant_changed = pyqtSignal(str, str)  # Emits (model_name, system_prompt)

    def __init__(self, assistants, parent=None):
        super().__init__(parent)
        print("\n=== Initializing Assistant Controls ===")
        self._assistants = assistants
        print(f">>> Found {len(assistants)} assistants")
        self._setup_ui()
        self._load_assistants()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Assistant selection
        assistant_layout = QHBoxLayout()
        self.assistant_combo = QComboBox()
        self.assistant_combo.currentTextChanged.connect(self._on_assistant_changed)
        assistant_layout.addWidget(QLabel("Assistant:"))
        assistant_layout.addWidget(self.assistant_combo, stretch=1)
        layout.addLayout(assistant_layout)

    def _load_assistants(self):
        """Load available assistants"""
        try:
            print("\n=== Loading Assistants ===")
            self.assistant_combo.clear()

            # Add "No Assistant" option for raw model access
            self.assistant_combo.addItem("No Assistant")
            print(">>> Added 'No Assistant' option")

            for assistant in self._assistants:
                print(f">>> Adding assistant: {assistant.name}")
                print(f"    Model: {assistant.model}")
                print(f"    Description: {assistant.description}")
                print(
                    f"    System Prompt: {assistant.system_prompt[:100]}..."
                )  # First 100 chars
                self.assistant_combo.addItem(assistant.name)

            print(f">>> Loaded {self.assistant_combo.count()} total options")

        except Exception as e:
            print(f"!!! Error loading assistants: {str(e)}")
            import traceback

            traceback.print_exc()

    def _on_assistant_changed(self, assistant_name: str):
        """Handle assistant selection change"""
        try:
            print(f"\n=== Assistant Changed: {assistant_name} ===")

            if assistant_name == "No Assistant":
                print(">>> Cleared assistant selection")
                self.assistant_changed.emit("", "")  # Clear system prompt
                return

            assistant = next(a for a in self._assistants if a.name == assistant_name)
            print(f">>> Selected assistant: {assistant_name}")
            print(f">>> Using model: {assistant.model}")
            print(
                f">>> System prompt: {assistant.system_prompt[:100]}..."
            )  # First 100 chars

            self.assistant_changed.emit(assistant.model, assistant.system_prompt)

        except Exception as e:
            print(f"!!! Error changing assistant: {str(e)}")
            import traceback

            traceback.print_exc()

    def get_current_assistant(self) -> Optional[AssistantConfig]:
        """Get the current assistant config if one is selected"""
        assistant_name = self.assistant_combo.currentText()
        if assistant_name == "No Assistant":
            return None

        return next(a for a in self._assistants if a.name == assistant_name)

    def get_current_system_prompt(self) -> Optional[str]:
        """Get the current assistant's system prompt"""
        assistant = self.get_current_assistant()
        if not assistant:
            print(">>> No assistant selected, no system prompt")
            return None

        print(f">>> Getting system prompt for: {assistant.name}")
        return assistant.system_prompt
