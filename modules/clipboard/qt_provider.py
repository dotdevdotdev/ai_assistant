from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from core.interfaces.clipboard import ClipboardProvider
from core.events import EventBus, Event, EventType


class QtClipboardProvider(ClipboardProvider):
    def __init__(self):
        self._event_bus = EventBus.get_instance()
        # Ensure we have a QApplication instance
        if not QApplication.instance():
            self.app = QApplication([])
        self._clipboard = QApplication.clipboard()

    def copy_to_clipboard(self, text: str) -> None:
        try:
            self._clipboard.setText(text, mode=self._clipboard.Mode.Clipboard)
        except Exception as e:
            self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    def get_clipboard_content(self) -> str:
        try:
            return self._clipboard.text(mode=self._clipboard.Mode.Clipboard)
        except Exception as e:
            self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
