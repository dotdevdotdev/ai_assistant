from abc import ABC, abstractmethod


class ClipboardProvider(ABC):
    @abstractmethod
    def copy_to_clipboard(self, text: str) -> None:
        """Copy text to system clipboard"""
        pass

    @abstractmethod
    def get_clipboard_content(self) -> str:
        """Get text content from system clipboard"""
        pass
