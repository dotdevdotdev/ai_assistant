from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
from .components.input_area import InputArea
from .components.audio_controls import AudioControls
from .components.llm_controls import LLMControls


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Assistant")
        self._setup_ui()

    def _setup_ui(self):
        # Create central widget and layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Add LLM controls at the top
        self.llm_controls = LLMControls()
        layout.addWidget(self.llm_controls)

        # Add audio controls
        self.audio_controls = AudioControls()
        layout.addWidget(self.audio_controls)

        # Add input area at the bottom
        self.input_area = InputArea()
        layout.addWidget(self.input_area)

        # Connect signals
        self.input_area.message_submitted.connect(self.llm_controls.send_message)
        self.audio_controls.transcription_ready.connect(
            self.input_area.text_edit.setText
        )
