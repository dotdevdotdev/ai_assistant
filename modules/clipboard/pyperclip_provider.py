import pyperclip
from core.interfaces.clipboard import ClipboardProvider
from core.events import EventBus, Event, EventType


class PyperclipProvider(ClipboardProvider):
    def __init__(self):
        self._event_bus = EventBus.get_instance()

    def copy_to_clipboard(self, text: str) -> None:
        try:
            pyperclip.copy(text)
        except Exception as e:
            self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise

    def get_clipboard_content(self) -> str:
        try:
            return pyperclip.paste()
        except Exception as e:
            self._event_bus.emit(Event(EventType.ERROR, error=e))
            raise
