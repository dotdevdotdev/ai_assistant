from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QSplitter,
    QHBoxLayout,
    QPushButton,
)
from PyQt6.QtCore import Qt, QSettings, QTimer
from .components.message_view import MessageView
from .components.input_area import InputArea
from .components.assistant_selector import AssistantSelector
from .components.audio_controls import AudioControls
from .components.tts_controls import TTSControls
from core.interfaces.assistant import Message, AssistantProvider
from core.interfaces.audio import (
    AudioInputProvider,
    AudioOutputProvider,
)
from core.interfaces.speech import (
    SpeechToTextProvider,
    TextToSpeechProvider,
)
from utils.registry import ProviderRegistry
from core.events import EventBus, Event, EventType
import asyncio
from typing import Optional, AsyncIterator
from PyQt6.QtWidgets import QApplication
import traceback
import io
from .components.llm_controls import LLMControls
from .components.assistant_controls import AssistantControls


class ChatWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._event_bus = EventBus.get_instance()
        self._settings = QSettings("AIAssistant", "Chat")
        self._setup_pending = True

    def set_app(self, app):
        """Set application instance and complete setup"""
        self.app = app
        if self._setup_pending:
            self.setup_ui()
            self.load_settings()
            self._setup_pending = False

    def setup_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setMinimumSize(800, 600)

        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Create splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top section with assistant selector and controls
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Add LLM controls first
        self.llm_controls = LLMControls()
        top_layout.addWidget(self.llm_controls)

        # Add Assistant controls
        self.assistant_controls = AssistantControls(self.app.config.assistants)
        self.assistant_controls.assistant_changed.connect(self._on_assistant_changed)
        top_layout.addWidget(self.assistant_controls)

        # Then audio controls
        self.audio_controls = AudioControls()
        self.audio_controls.recording_started.connect(self._on_recording_started)
        self.audio_controls.recording_stopped.connect(self._on_recording_stopped)
        self.audio_controls.transcription_ready.connect(self._on_transcription_ready)
        top_layout.addWidget(self.audio_controls)

        # Add TTS controls below audio controls
        self.tts_controls = TTSControls()
        self.tts_controls.tts_generated.connect(self._on_tts_generated)
        top_layout.addWidget(self.tts_controls)

        # Add Full Pipeline button to top section
        pipeline_layout = QHBoxLayout()
        self.pipeline_button = QPushButton("🎙️ Record → Text → LLM → Speech")
        self.pipeline_button.setToolTip(
            "Record audio, convert to text, get LLM response, and play as speech"
        )
        self.pipeline_button.setCheckable(True)
        self.pipeline_button.clicked.connect(self._on_pipeline_clicked)
        pipeline_layout.addWidget(self.pipeline_button)
        top_layout.addLayout(pipeline_layout)

        # Message view
        self.message_view = MessageView()

        # Input area
        self.input_area = InputArea()
        self.input_area.message_submitted.connect(self._on_message_submitted)
        self.input_area.recording_toggled.connect(
            self.audio_controls.record_button.setChecked
        )

        # Connect LLM response to message view through our handler
        self.llm_controls.response_ready.connect(self._on_llm_response)

        # Add widgets to splitter
        splitter.addWidget(top_widget)
        splitter.addWidget(self.message_view)
        splitter.addWidget(self.input_area)

        # Set stretch factors
        splitter.setStretchFactor(0, 0)  # Top section - fixed
        splitter.setStretchFactor(1, 1)  # Message view - stretches
        splitter.setStretchFactor(2, 0)  # Input area - fixed

        layout.addWidget(splitter)

    def _get_username(self) -> str:
        """Get username from config or default to 'User'"""
        return self.app.config.ui.get("username", "User")

    def _on_message_submitted(self, message: str):
        """Handle user message submission"""
        # Add user message to view with proper name immediately
        username = self._get_username()
        user_message = Message(username, message)
        self.message_view.add_message(user_message)

        # Forward to LLM controls asynchronously
        QTimer.singleShot(0, lambda: self.llm_controls.send_message(message))

    def _on_llm_response(self, response: str):
        """Handle regular (non-pipeline) LLM response"""
        try:
            # Disconnect to prevent duplicate responses
            self.llm_controls.response_ready.disconnect(self._on_llm_response)

            # Add assistant message to view
            assistant_message = Message("Assistant", response)
            self.message_view.add_message(assistant_message)

        except Exception as e:
            print(f"!!! Error handling LLM response: {e}")

    def _on_model_changed(self, model: str, config: dict):
        # Update the assistant configuration
        pass

    def _on_recording_started(self):
        print("Recording started, disabling input area")
        self.input_area.setEnabled(False)
        # Temporarily disable transcription
        # self._start_transcription()

    def _on_recording_stopped(self):
        """Handle regular recording stop"""
        print(">>> Regular recording stop handler")
        # Only proceed if NOT in pipeline mode
        if self.pipeline_button.isChecked():
            print(">>> Pipeline active - skipping regular recording handler")
            return

        print("Recording stopped, enabling input area")
        self.input_area.setEnabled(True)

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

    def _setup_tts_controls(self):
        tts_layout = QHBoxLayout()

        self.tts_button = QPushButton("🔊 TTS")
        self.tts_button.setToolTip(
            "Convert to speech using last recording as voice reference"
        )
        self.tts_button.clicked.connect(self._on_tts_clicked)

        tts_layout.addWidget(self.tts_button)
        self.input_area.layout().addLayout(tts_layout)

    async def _on_tts_clicked(self):
        """Handle TTS button click"""
        try:
            text = self.input_area.text_edit.toPlainText().strip()
            if not text:
                return

            # Get TTS provider
            tts_provider = self.registry.get_provider(TextToSpeechProvider)

            # Convert text to speech
            audio_data = await tts_provider.synthesize(text)

            # Use AudioInputProvider here too
            audio_provider = self.registry.get_provider(AudioInputProvider)
            audio_provider.play_audio(io.BytesIO(audio_data))

        except Exception as e:
            print(f"!!! Error during TTS: {e}")
            print(traceback.format_exc())

    def _on_tts_generated(self, audio_data: bytes):
        """Handle TTS generated audio"""
        try:
            # Use AudioInputProvider instead of AudioOutputProvider since that's what we registered
            audio_provider = ProviderRegistry.get_instance().get_provider(
                AudioInputProvider
            )
            audio_provider.play_audio(io.BytesIO(audio_data))
        except Exception as e:
            print(f"!!! Error playing TTS audio: {e}")
            print(traceback.format_exc())

    def _on_transcription_ready(self, text: str):
        """Handle transcribed text"""
        # Update input area
        self.input_area.text_edit.setPlainText(text)
        self.input_area.send_button.setEnabled(True)

        # IMPORTANT: Only proceed if NOT in pipeline mode
        if self.pipeline_button.isChecked():
            print(">>> Pipeline active - skipping regular transcription handler")
            return

        # Regular non-pipeline transcription handling
        print(">>> Regular transcription handler: Sending text to LLM")
        username = self._get_username()
        user_message = Message(username, text)
        self.message_view.add_message(user_message)

        # Send to LLM - ensure we're using a fresh connection
        try:
            self.llm_controls.response_ready.disconnect(self._on_llm_response)
        except:
            pass
        self.llm_controls.response_ready.connect(self._on_llm_response)
        self.llm_controls.send_message(text)

    def _on_assistant_changed(self, model: str, system_prompt: str):
        """Handle assistant selection"""
        if model:  # If an assistant was selected
            # Find the provider:model format
            for provider_name, provider in self.app._llm_providers.items():
                if model in provider.get_available_models():
                    full_model = f"{provider_name}: {model}"
                    self.llm_controls.model_combo.setCurrentText(full_model)
                    break

    def _on_pipeline_clicked(self, checked: bool):
        """Handle full pipeline button click"""
        try:
            if checked:
                print("\n=== Starting Pipeline Mode ===")

                # Disable input area at the start of pipeline
                self.input_area.setEnabled(False)

                # Clean up any existing connections first
                self._cleanup_pipeline_connections()

                # Temporarily disconnect ALL regular handlers
                try:
                    self.audio_controls.transcription_ready.disconnect()  # Disconnect all slots
                    self.audio_controls.recording_stopped.disconnect()  # Disconnect all slots
                    self.llm_controls.response_ready.disconnect()  # Disconnect all slots
                except:
                    pass

                print(">>> Step 1: Starting audio recording")
                self.pipeline_button.setText("🔴 Stop Pipeline")

                # Connect pipeline-specific handlers
                print(">>> Connecting pipeline recording handler")
                self.audio_controls.recording_stopped.connect(
                    self._on_pipeline_recording_stopped,
                    type=Qt.ConnectionType.UniqueConnection,
                )

                print(">>> Connecting pipeline transcription handler")
                self.audio_controls.transcription_ready.connect(
                    self._on_pipeline_transcription,
                    type=Qt.ConnectionType.UniqueConnection,
                )

                # Start recording directly through audio controls
                self.audio_controls.record_button.setChecked(True)
                self.audio_controls._on_record_clicked(True)
            else:
                print("\n=== Stopping Pipeline Mode ===")
                print(">>> Step 2: Stopping audio recording")

                # Stop recording through audio controls
                self.audio_controls.record_button.setChecked(False)
                self.audio_controls._on_record_clicked(False)

        except Exception as e:
            print(f"!!! Error in pipeline control: {e}")
            self._end_pipeline()

    def _cleanup_pipeline_connections(self):
        """Clean up all pipeline-related signal connections"""
        print("\n=== Cleaning up pipeline connections ===")

        try:
            print(">>> Disconnecting pipeline recording handler")
            self.audio_controls.recording_stopped.disconnect(
                self._on_pipeline_recording_stopped
            )
        except Exception as e:
            print(f">>> Recording handler not connected: {e}")

        try:
            print(">>> Disconnecting pipeline transcription handler")
            self.audio_controls.transcription_ready.disconnect(
                self._on_pipeline_transcription
            )
        except Exception as e:
            print(f">>> Transcription handler not connected: {e}")

        try:
            print(">>> Disconnecting pipeline LLM handler")
            self.llm_controls.response_ready.disconnect(self._on_pipeline_llm_response)
        except Exception as e:
            print(f">>> LLM handler not connected: {e}")

        try:
            print(">>> Disconnecting pipeline TTS handler")
            self.tts_controls.tts_generated.disconnect(self._on_pipeline_tts_complete)
        except Exception as e:
            print(f">>> TTS handler not connected: {e}")

    def _on_pipeline_recording_stopped(self):
        """Handle recording stop in pipeline"""
        print(">>> Step 3: Recording stopped, waiting for transcription")

        # Verify the speech provider is ready
        speech_provider = ProviderRegistry.get_instance().get_provider(
            SpeechToTextProvider
        )
        if not speech_provider:
            print("!!! Speech provider not found")
            self.pipeline_button.setChecked(False)
            self._cleanup_pipeline_connections()
            return

    def _on_pipeline_transcription(self, text: str):
        """Handle transcription in pipeline"""
        print(f"\n>>> Step 4: Got transcription: {text}")

        if not text.strip():
            print("!!! Empty transcription received")
            self._end_pipeline()
            return

        # Immediately show user message in chat
        username = self._get_username()
        user_message = Message(username, text)
        self.message_view.add_message(user_message)

        # Update input area text
        self.input_area.text_edit.setPlainText(text)

        # Process events to update UI immediately
        QApplication.processEvents()

        # Clean up any existing LLM response connection
        try:
            self.llm_controls.response_ready.disconnect(self._on_pipeline_llm_response)
        except:
            pass

        # Send to LLM
        print(">>> Step 5: Sending to LLM for response")
        self.llm_controls.response_ready.connect(self._on_pipeline_llm_response)
        self.llm_controls.send_message(text)

    def _on_pipeline_llm_response(self, response: str):
        """Handle LLM response in pipeline"""
        print(f"\n>>> Step 6: Got LLM response")

        # Disconnect LLM handler immediately
        self.llm_controls.response_ready.disconnect(self._on_pipeline_llm_response)

        # Check if response is an error message
        if response.startswith("Error:") or "error" in response.lower():
            print("!!! LLM returned an error, stopping pipeline")
            self._end_pipeline()
            return

        # Immediately show assistant message in chat
        assistant_message = Message("Assistant", response)
        self.message_view.add_message(assistant_message)

        # Process events to update UI immediately
        QApplication.processEvents()

        # Clean up any existing TTS connection
        try:
            self.tts_controls.tts_generated.disconnect(self._on_pipeline_tts_complete)
        except:
            pass

        print(">>> Step 7: Sending to TTS for speech synthesis")
        self.tts_controls.tts_generated.connect(self._on_pipeline_tts_complete)

        try:
            loop = asyncio.get_event_loop()
            synthesis_task = loop.create_task(
                self.tts_controls.synthesize_text(response)
            )

            def handle_synthesis_error(task):
                try:
                    task.result()
                except Exception as e:
                    print(f"!!! Error in TTS synthesis task: {e}")
                    self._end_pipeline()

            synthesis_task.add_done_callback(handle_synthesis_error)

        except Exception as e:
            print(f"!!! Error starting TTS synthesis: {e}")
            self._end_pipeline()

    def _end_pipeline(self):
        """Clean up and end the pipeline"""
        print("\n=== Ending Pipeline Mode ===")
        self.pipeline_button.setChecked(False)
        self.pipeline_button.setText("🎙️ Record → Text → LLM → Speech")

        # Clean up pipeline connections
        self._cleanup_pipeline_connections()

        # Re-enable input area
        self.input_area.setEnabled(True)

        # Reconnect regular handlers
        print(">>> Reconnecting regular handlers")
        self.audio_controls.transcription_ready.connect(
            self._on_transcription_ready, type=Qt.ConnectionType.UniqueConnection
        )
        self.audio_controls.recording_stopped.connect(
            self._on_recording_stopped, type=Qt.ConnectionType.UniqueConnection
        )

    def _on_pipeline_tts_complete(self, audio_data: bytes):
        """Handle TTS completion in pipeline"""
        try:
            if not audio_data:
                print("!!! No audio data received from TTS")
                self._end_pipeline()
                return

            print(">>> Pipeline completed successfully")

        except Exception as e:
            print(f"!!! Error in TTS completion handler: {e}")
        finally:
            # End the pipeline after TTS completes
            self._end_pipeline()


# TODO: Audio Integration Status
# - Basic audio playback working for recordings
# - TTS playback needs verification
# - Consider adding:
#   1. Volume control for TTS playback
#   2. Progress indicator during TTS generation
#   3. Error feedback in UI
#   4. Queue system for multiple TTS requests
