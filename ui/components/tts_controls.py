from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QTextEdit,
    QFileDialog,
)
from PyQt6.QtCore import pyqtSignal
from core.interfaces.speech import TextToSpeechProvider
from utils.registry import ProviderRegistry
import os
import io
import asyncio
from qasync import asyncSlot


class TTSControls(QWidget):
    tts_generated = pyqtSignal(bytes)  # Emitted when TTS generates audio

    def __init__(self, reference_dir: str = "reference_audio", parent=None):
        super().__init__(parent)
        print("\n=== Initializing TTS Controls ===")
        self._reference_dir = reference_dir
        self._provider = ProviderRegistry.get_instance().get_provider(
            TextToSpeechProvider
        )
        self._setup_ui()
        self._load_reference_files()

        # Create reference directory if it doesn't exist
        os.makedirs(self._reference_dir, exist_ok=True)
        print(">>> TTS Controls initialized")

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Reference audio selection
        ref_layout = QHBoxLayout()
        self.ref_combo = QComboBox()
        self.ref_combo.setMinimumWidth(200)
        self.refresh_button = QPushButton("🔄")
        self.refresh_button.setToolTip("Refresh reference audio files")
        self.refresh_button.clicked.connect(self._load_reference_files)
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self._browse_reference_audio)

        ref_layout.addWidget(QLabel("Reference Audio:"))
        ref_layout.addWidget(self.ref_combo, stretch=1)
        ref_layout.addWidget(self.refresh_button)
        ref_layout.addWidget(self.browse_button)

        # Text input
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Enter text to synthesize...")
        self.text_edit.setMaximumHeight(100)

        # Generate button
        button_layout = QHBoxLayout()
        self.generate_button = QPushButton("🔊 Generate Speech")
        self.generate_button.setStyleSheet(
            "QPushButton:hover { background-color: #444; }"
        )
        # Connect directly to the async method - remove the wrapper
        self.generate_button.clicked.connect(self._on_generate_clicked)
        button_layout.addStretch()
        button_layout.addWidget(self.generate_button)

        layout.addLayout(ref_layout)
        layout.addWidget(self.text_edit)
        layout.addLayout(button_layout)

    def _load_reference_files(self):
        """Load available reference audio files"""
        self.ref_combo.clear()
        if os.path.exists(self._reference_dir):
            for file in os.listdir(self._reference_dir):
                if file.endswith(".wav"):  # Only list WAV files
                    self.ref_combo.addItem(
                        file, os.path.join(self._reference_dir, file)
                    )

    def _browse_reference_audio(self):
        """Open file dialog to select reference audio"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Reference Audio",
            "",
            "WAV Files (*.wav)",  # Changed to only allow WAV files
        )
        if file_path:
            # Copy file to reference directory
            filename = os.path.basename(file_path)
            dest_path = os.path.join(self._reference_dir, filename)
            if file_path != dest_path:
                import shutil

                shutil.copy2(file_path, dest_path)
            self._load_reference_files()
            # Select the newly added file
            index = self.ref_combo.findText(filename)
            if index >= 0:
                self.ref_combo.setCurrentIndex(index)

    @asyncSlot()
    async def _on_generate_clicked(self):
        """Handle generate button click"""
        print("\n=== Generate Speech button clicked ===")  # Moved from wrapper
        print(">>> Starting speech generation")
        try:
            text = self.text_edit.toPlainText().strip()
            if not text:
                print("!!! No text to synthesize")
                return

            ref_audio = self.ref_combo.currentData()
            if not ref_audio:
                print("!!! No reference audio selected")
                return

            print(f">>> Using reference audio: {ref_audio}")
            print(f">>> Generating speech for text: {text}")

            # Disable controls during generation
            self.generate_button.setEnabled(False)
            self.text_edit.setEnabled(False)

            try:
                # Generate audio
                print(">>> Calling TTS provider synthesize method")
                audio_data = await self._provider.synthesize(text, ref_audio)
                print(">>> TTS generation completed, emitting result")
                self.tts_generated.emit(audio_data)
            finally:
                # Re-enable controls
                print(">>> Re-enabling controls")
                self.generate_button.setEnabled(True)
                self.text_edit.setEnabled(True)

        except Exception as e:
            print(f"!!! Error generating TTS: {e}")
            import traceback

            print(traceback.format_exc())
