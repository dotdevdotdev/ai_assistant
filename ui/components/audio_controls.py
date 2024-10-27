from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QComboBox,
    QLabel,
    QProgressBar,
    QApplication,  # Add this import
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from core.interfaces.audio import AudioInputProvider, AudioConfig
from utils.registry import ProviderRegistry
import numpy as np
import traceback
import os
from datetime import datetime
import io
import wave
import pkg_resources
import pathlib
import struct


class AudioControls(QWidget):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()
    input_device_changed = pyqtSignal(int)
    output_device_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._provider = ProviderRegistry.get_instance().get_provider(
            AudioInputProvider
        )
        self._recording = False
        self._setup_ui()
        self._load_devices()
        self._recordings_dir = "recordings"

        # Create directories
        self._resources_dir = (
            pathlib.Path(__file__).parent.parent.parent / "resources" / "audio"
        )
        self._resources_dir.mkdir(parents=True, exist_ok=True)
        os.makedirs(self._recordings_dir, exist_ok=True)

        # Ensure test sound exists
        self._test_sound_path = self._resources_dir / "test-sound.wav"
        if not self._test_sound_path.exists():
            self._create_test_sound_file()

    def _create_test_sound_file(self):
        """Create a test sound file if it doesn't exist"""
        try:
            # Create a louder test sound
            duration = 0.5  # seconds
            sample_rate = 44100
            t = np.linspace(0, duration, int(sample_rate * duration))

            # Create a sound that starts at 880Hz and goes down to 440Hz
            freq = np.linspace(880, 440, len(t))
            sound = np.sin(2 * np.pi * freq * t)

            # Make the sound louder (80% of max volume)
            sound = sound * 0.8

            # Apply an envelope to avoid clicks
            envelope = np.exp(-3 * t)
            sound = sound * envelope

            # Convert to int16 at near-maximum volume
            sound = (sound * 32767).astype(np.int16)

            # Verify sound data
            max_value = np.max(np.abs(sound))
            print(f">>> Test sound max value: {max_value} (max possible: 32767)")

            # Save as WAV
            with wave.open(str(self._test_sound_path), "wb") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(sound.tobytes())

            print(f">>> Created test sound file at {self._test_sound_path}")

            # Verify the saved file
            with wave.open(str(self._test_sound_path), "rb") as wf:
                print(f">>> Verified WAV file:")
                print(f"    Channels: {wf.getnchannels()}")
                print(f"    Sample width: {wf.getsampwidth()}")
                print(f"    Frame rate: {wf.getframerate()}")
                print(f"    Frames: {wf.getnframes()}")

                # Read and verify first chunk
                data = wf.readframes(1024)
                if len(data) > 0:
                    sample_values = struct.unpack(f"<{len(data)//2}h", data)
                    max_value = max(abs(min(sample_values)), abs(max(sample_values)))
                    print(f">>> Max value in first chunk: {max_value}")

        except Exception as e:
            print(f"!!! Error creating test sound: {e}")
            print(traceback.format_exc())

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Device selection
        devices_layout = QVBoxLayout()

        # Input device selection
        input_layout = QHBoxLayout()
        self.input_combo = QComboBox()
        self.input_combo.currentIndexChanged.connect(self._on_input_device_changed)
        input_layout.addWidget(QLabel("Input Device:"))
        input_layout.addWidget(self.input_combo, stretch=1)

        # Output device selection
        output_layout = QHBoxLayout()
        self.output_combo = QComboBox()
        self.output_combo.currentIndexChanged.connect(self._on_output_device_changed)
        output_layout.addWidget(QLabel("Output Device:"))
        output_layout.addWidget(self.output_combo, stretch=1)

        # Test sound button
        self.test_sound_button = QPushButton("Test Output")
        self.test_sound_button.clicked.connect(self._on_test_sound_clicked)
        output_layout.addWidget(self.test_sound_button)

        devices_layout.addLayout(input_layout)
        devices_layout.addLayout(output_layout)

        # Audio level indicator
        self.level_indicator = QProgressBar()
        self.level_indicator.setRange(0, 100)
        self.level_indicator.setTextVisible(False)
        self.level_indicator.setFixedHeight(10)

        # Controls layout
        controls_layout = QHBoxLayout()

        # Record button
        self.record_button = QPushButton("Start Recording")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self._on_record_clicked)

        # Play button
        self.play_button = QPushButton("Play Recording")
        self.play_button.clicked.connect(self._on_play_clicked)
        self.play_button.setEnabled(False)

        controls_layout.addWidget(self.record_button)
        controls_layout.addWidget(self.play_button)

        layout.addLayout(devices_layout)
        layout.addWidget(self.level_indicator)
        layout.addLayout(controls_layout)

        # Timer for updating audio level - increase interval to reduce load
        self._level_timer = QTimer()
        self._level_timer.timeout.connect(self._update_audio_level)
        self._level_timer.setInterval(100)  # Update every 100ms instead of 200ms

    def _generate_test_tone(self) -> bytes:
        """Generate a short test tone"""
        duration = 0.5  # seconds
        sample_rate = 44100
        frequency = 440  # Hz (A4 note)
        samples = np.arange(int(duration * sample_rate))
        tone = np.sin(2 * np.pi * frequency * samples / sample_rate)
        tone = (tone * 32767).astype(np.int16)
        return tone.tobytes()

    def _on_test_sound_clicked(self):
        """Play test sound through the selected output device"""
        try:
            print("\n=== Playing test sound ===")
            output_device_id = self.output_combo.currentData()
            self._provider.set_output_device(output_device_id)
            print(f">>> Using output device ID: {output_device_id}")
            print(f">>> Playing test sound from: {self._test_sound_path}")

            # Disable buttons during playback
            self.test_sound_button.setEnabled(False)
            self.play_button.setEnabled(False)
            self.record_button.setEnabled(False)

            try:
                # Open and read the test sound file
                with open(self._test_sound_path, "rb") as f:
                    wav_data = io.BytesIO(f.read())

                # Play the test sound
                self._provider.play_audio(wav_data)
                print(">>> Test sound completed")

            finally:
                # Re-enable buttons
                self.test_sound_button.setEnabled(True)
                self.play_button.setEnabled(True)
                self.record_button.setEnabled(True)

        except Exception as e:
            print(f"!!! Error playing test sound: {str(e)}")
            print(traceback.format_exc())

    def _save_recording(self):
        """Save the recording to a file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self._recordings_dir, f"recording_{timestamp}.wav")
            self._provider.save_recording(filename)
        except Exception as e:
            print(f"!!! Error saving recording: {str(e)}")
            print(traceback.format_exc())

    def _load_devices(self):
        devices = self._provider.get_devices()
        default_input_name = None
        default_output_name = None

        try:
            registry = ProviderRegistry.get_instance()
            config = registry.get_provider_config(AudioInputProvider)
            default_input_name = config.get("input_device")
            default_output_name = config.get("output_device")
        except Exception as e:
            print(f"!!! Error getting device config: {e}")

        # Load input devices
        input_devices = devices.get("input", [])
        default_input_index = 0
        for i, device in enumerate(input_devices):
            self.input_combo.addItem(device["name"], device["id"])
            if default_input_name and default_input_name in device["name"]:
                default_input_index = i

        if self.input_combo.count() > 0:
            self.input_combo.setCurrentIndex(default_input_index)
            print(f">>> Using input device: {self.input_combo.currentText()}")

        # Load output devices
        output_devices = devices.get("output", [])
        default_output_index = 0
        for i, device in enumerate(output_devices):
            self.output_combo.addItem(device["name"], device["id"])
            if default_output_name and default_output_name in device["name"]:
                default_output_index = i

        if self.output_combo.count() > 0:
            self.output_combo.setCurrentIndex(default_output_index)
            print(f">>> Using output device: {self.output_combo.currentText()}")

    def _on_input_device_changed(self, index: int):
        if index >= 0:
            device_id = self.input_combo.currentData()
            self.input_device_changed.emit(device_id)

    def _on_output_device_changed(self, index: int):
        if index >= 0:
            device_id = self.output_combo.currentData()
            print(f">>> Setting output device ID to: {device_id}")
            self._provider.set_output_device(device_id)  # Set the output device
            self.output_device_changed.emit(device_id)

    def _on_record_clicked(self, checked: bool):
        self._recording = checked
        self.record_button.setText("Stop Recording" if checked else "Start Recording")

        # Disable buttons during recording and processing
        self.play_button.setEnabled(False)
        self.test_sound_button.setEnabled(False)

        if checked:
            print("\n=== Starting audio recording ===")
            try:
                device_id = self.input_combo.currentData()
                devices = self._provider.get_devices()
                input_devices = devices.get("input", [])
                device_info = next(d for d in input_devices if d["id"] == device_id)

                config = AudioConfig(
                    sample_rate=int(device_info["sample_rate"]),
                    channels=1,
                    chunk_size=1024,
                    device_id=device_id,
                )
                print(f">>> Audio config: {config}")

                self._provider.start_stream(config)
                self._level_timer.start()
                self.recording_started.emit()

            except Exception as e:
                print(f"!!! Error starting recording: {str(e)}")
                print(traceback.format_exc())
                self._recording = False
                self.record_button.setChecked(False)
                self.play_button.setEnabled(True)
                self.test_sound_button.setEnabled(True)
                return
        else:
            print("\n=== Requesting recording stop ===")
            self._level_timer.stop()
            self.level_indicator.setValue(0)

            # Disable all controls during processing
            self.record_button.setEnabled(False)
            self.play_button.setEnabled(False)
            self.test_sound_button.setEnabled(False)

            # Stop the stream and wait for processing
            self._provider.stop_stream()

            # Wait for processing to complete
            while self._provider.is_processing():
                QApplication.processEvents()  # Keep UI responsive

            self._save_recording()  # Save the recording
            self.recording_stopped.emit()

            # Re-enable controls
            self.record_button.setEnabled(True)
            self.play_button.setEnabled(True)
            self.test_sound_button.setEnabled(True)

    def _on_play_clicked(self):
        print("\n=== Playing recorded audio ===")
        try:
            self.play_button.setEnabled(False)
            self.record_button.setEnabled(False)

            # Get output device ID and ensure it's set
            output_device_id = self.output_combo.currentData()
            self._provider.set_output_device(output_device_id)
            print(f">>> Using output device ID: {output_device_id}")

            # Play the recorded audio
            self._provider.play_audio(None)

            self.play_button.setEnabled(True)
            self.record_button.setEnabled(True)
        except Exception as e:
            print(f"!!! Error playing audio: {str(e)}")
            print(traceback.format_exc())
            self.play_button.setEnabled(True)
            self.record_button.setEnabled(True)

    def _update_audio_level(self):
        if not self._recording:
            return

        try:
            chunk = self._provider.read_chunk()
            if not chunk:
                return

            audio_data = np.frombuffer(chunk, dtype=np.int16)
            if len(audio_data) == 0:
                return

            max_value = np.max(np.abs(audio_data))
            level = int((max_value / 32768.0) * 100)
            self.level_indicator.setValue(level)

        except Exception as e:
            print(f"!!! Error reading audio chunk: {str(e)}")
            print(traceback.format_exc())

    def is_recording(self) -> bool:
        return self._recording
