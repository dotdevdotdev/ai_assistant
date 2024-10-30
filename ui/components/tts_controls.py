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
from modules.speech.composite_tts_provider import CompositeTTSProvider
import os
import io
import asyncio
from qasync import asyncSlot
import traceback


# TODO: TTS Integration Status
# - Basic UI and async handling is working
# - F5-TTS provider is registered but not generating audio
# - Need to verify F5-TTS CLI installation and dependencies
# - May need to add progress indication during generation
# - Consider adding volume control for TTS output
# - Consider adding voice selection/management features


class TTSControls(QWidget):
    tts_generated = pyqtSignal(bytes)  # Emitted when TTS generates audio

    def __init__(self, reference_dir: str = "reference_audio", parent=None):
        super().__init__(parent)
        print("\n=== Initializing TTS Controls ===")
        self._reference_dir = reference_dir
        self._setup_ui()
        self._load_reference_files()

        # Create reference directory if it doesn't exist
        os.makedirs(self._reference_dir, exist_ok=True)

        # Get initial provider info
        provider = self._get_provider()
        if isinstance(provider, CompositeTTSProvider):
            active = provider.get_active_provider()
            available = provider.get_available_providers()
            print(f">>> Available TTS providers: {available}")
            print(f">>> Active TTS provider: {active}")

        print(">>> TTS Controls initialized")

    def _get_provider(self) -> TextToSpeechProvider:
        """Get the current TTS provider"""
        return ProviderRegistry.get_instance().get_provider(TextToSpeechProvider)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Provider selection
        provider_layout = QHBoxLayout()
        self.provider_combo = QComboBox()
        provider = self._get_provider()
        if isinstance(provider, CompositeTTSProvider):
            self.provider_combo.addItems(provider.get_available_providers())
            self.provider_combo.setCurrentText(provider.get_active_provider())
            self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addWidget(QLabel("TTS Provider:"))
        provider_layout.addWidget(self.provider_combo, stretch=1)
        layout.addLayout(provider_layout)

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
                audio_data = await self._get_provider().synthesize(text, ref_audio)
                print(">>> TTS generation completed, emitting result")
                self.tts_generated.emit(audio_data)
            finally:
                # Re-enable controls
                print(">>> Re-enabling controls")
                self.generate_button.setEnabled(True)
                self.text_edit.setEnabled(True)

        except Exception as e:
            print(f"!!! Error generating TTS: {e}")
            print(traceback.format_exc())

    async def synthesize_text(self, text: str):
        """Convert text to speech using the selected TTS provider"""
        try:
            print(">>> Starting TTS synthesis")
            tts_provider = self._get_provider()

            if not tts_provider:
                print("!!! No TTS provider found")
                return

            # Get currently selected reference audio
            ref_audio = self.ref_combo.currentData()
            if not ref_audio:
                print("!!! No reference audio selected, using first available")
                # Try to use first available reference audio
                if self.ref_combo.count() > 0:
                    ref_audio = self.ref_combo.itemData(0)
                else:
                    print("!!! No reference audio files available")
                    return

            print(f">>> Using reference audio: {ref_audio}")

            # Generate audio data with reference audio
            audio_data = await tts_provider.synthesize(text, ref_audio)

            # Emit the generated audio data
            print(">>> TTS synthesis complete, emitting audio data")
            self.tts_generated.emit(audio_data)

        except Exception as e:
            print(f"!!! Error during TTS synthesis: {e}")
            print(traceback.format_exc())

    def _on_tts_clicked(self):
        """Handle TTS button click - can be used for manual TTS triggering"""
        # Implementation for manual TTS button if needed
        pass

    def _on_provider_changed(self, provider_name: str):
        """Handle provider selection change"""
        try:
            provider = self._get_provider()
            if isinstance(provider, CompositeTTSProvider):
                provider.set_active_provider(provider_name)
                print(f">>> Switched to TTS provider: {provider_name}")
        except Exception as e:
            print(f"!!! Error changing TTS provider: {e}")
