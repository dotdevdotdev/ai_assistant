from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, QSettings
from .components.message_view import MessageView
from .components.input_area import InputArea
from .components.assistant_selector import AssistantSelector
from .components.audio_controls import AudioControls
from core.interfaces.assistant import Message, AssistantProvider
from core.interfaces.audio import AudioInputProvider  # Add this import
from core.interfaces.speech import SpeechToTextProvider
from utils.registry import ProviderRegistry
from core.events import EventBus, Event, EventType
import asyncio
from typing import Optional, AsyncIterator
from PyQt6.QtWidgets import QApplication


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._event_bus = EventBus.get_instance()
        self._settings = QSettings("AIAssistant", "Chat")
        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(800, 600)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section with assistant selector and audio controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        self.assistant_selector = AssistantSelector()
        self.assistant_selector.model_changed.connect(self._on_model_changed)

        self.audio_controls = AudioControls()
        self.audio_controls.recording_started.connect(self._on_recording_started)
        self.audio_controls.recording_stopped.connect(self._on_recording_stopped)

        top_layout.addWidget(self.assistant_selector)
        top_layout.addWidget(self.audio_controls)

        # Message view
        self.message_view = MessageView()

        # Input area
        self.input_area = InputArea()
        self.input_area.message_submitted.connect(self._on_message_submitted)
        self.input_area.recording_toggled.connect(
            self.audio_controls.record_button.setChecked
        )

        # Add widgets to splitter
        splitter.addWidget(top_widget)
        splitter.addWidget(self.message_view)
        splitter.addWidget(self.input_area)

        # Set stretch factors
        splitter.setStretchFactor(0, 0)  # Top section - fixed
        splitter.setStretchFactor(1, 1)  # Message view - stretches
        splitter.setStretchFactor(2, 0)  # Input area - fixed

        layout.addWidget(splitter)

    async def _on_message_submitted(self, text: str):
        # Add user message to view
        user_message = Message("user", text)
        self.message_view.add_message(user_message)

        # Get assistant response
        try:
            assistant = ProviderRegistry.get_instance().get_provider(AssistantProvider)
            messages = self.message_view.get_messages()

            # Create assistant message placeholder
            assistant_message = Message("assistant", "")
            self.message_view.add_message(assistant_message)

            full_response = ""
            async for chunk in assistant.send_message(messages):
                full_response += chunk
                assistant_message.content = full_response
                # Need to implement message update mechanism

        except Exception as e:
            await self._event_bus.emit(Event(EventType.ERROR, error=e))

    def _on_model_changed(self, model: str, config: dict):
        # Update the assistant configuration
        pass

    def _on_recording_started(self):
        print("Recording started, disabling input area")
        self.input_area.setEnabled(False)
        # Temporarily disable transcription
        # self._start_transcription()

    def _on_recording_stopped(self):
        print("Recording stopped, enabling input area")
        self.input_area.setEnabled(True)
        # Temporarily disable transcription
        # self._stop_transcription()

    def _start_transcription(self):
        print("Starting transcription process")
        try:
            self.speech_provider = ProviderRegistry.get_instance().get_provider(
                SpeechToTextProvider
            )
            self.audio_provider = ProviderRegistry.get_instance().get_provider(
                AudioInputProvider
            )

            if self.speech_provider:
                print("Found speech provider, setting up transcription stream")
                # Get the current event loop
                loop = asyncio.get_event_loop()
                # Start the transcription task
                self.transcription_task = loop.create_task(self._transcription_loop())
            else:
                print("No speech provider found!")
        except Exception as e:
            print(f"Error setting up transcription: {e}")

    def _stop_transcription(self):
        print("Stopping transcription process")
        if hasattr(self, "transcription_task"):
            self.transcription_task.cancel()
            delattr(self, "transcription_task")

    async def _transcription_loop(self):
        """Process audio chunks and get transcriptions"""
        print("\n=== Starting transcription loop ===")
        try:

            class AudioStreamIterator:
                def __init__(self, audio_provider):
                    self.audio_provider = audio_provider

                def __aiter__(
                    self,
                ):  # Remove async - __aiter__ should return self directly
                    return self

                async def __anext__(self):  # Keep this async
                    try:
                        chunk = self.audio_provider.read_chunk()
                        if chunk:
                            return chunk
                        raise StopAsyncIteration
                    except Exception as e:
                        print(f"!!! Error reading audio chunk: {e}")
                        raise StopAsyncIteration

            print("Starting transcription stream processing")
            audio_iterator = AudioStreamIterator(self.audio_provider)

            # Remove the await here - transcribe_stream returns an async generator
            async for transcription in self.speech_provider.transcribe_stream(
                audio_iterator
            ):
                if transcription.strip():
                    print(f"\n>>> Transcription received in UI: '{transcription}'")

                    # Update UI in thread-safe way
                    try:
                        print("Attempting to update UI...")
                        self.input_area.text_edit.setPlainText(transcription)
                        self.input_area.send_button.setEnabled(True)
                        QApplication.instance().processEvents()
                        print("UI successfully updated with transcription")
                    except Exception as e:
                        print(f"!!! Error updating UI: {e}")

        except asyncio.CancelledError:
            print(">>> Transcription loop cancelled")
        except Exception as e:
            print(f"!!! Error in transcription loop: {e}")
            await self._event_bus.emit(Event(EventType.ERROR, error=e))

    def load_settings(self):
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

    def save_settings(self):
        self._settings.setValue("geometry", self.saveGeometry())

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)
