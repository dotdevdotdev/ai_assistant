from enum import Enum
from core.interfaces.clipboard import ClipboardProvider
from .qt_provider import QtClipboardProvider
from .pyperclip_provider import PyperclipProvider


class ClipboardProviderType(Enum):
    QT = "qt"
    PYPERCLIP = "pyperclip"


def create_clipboard_provider(provider_type: str) -> ClipboardProvider:
    providers = {
        "qt": QtClipboardProvider,
        "pyperclip": PyperclipProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unknown clipboard provider type: {provider_type}")

    return providers[provider_type]()
