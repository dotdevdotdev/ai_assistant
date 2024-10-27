from PyQt6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from core.interfaces.assistant import Message


class MessageWidget(QWidget):
    def __init__(self, message: Message, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        role_label = QLabel(f"{message.role.capitalize()}:")
        role_label.setStyleSheet(
            f"font-weight: bold; color: {'#0078d4' if message.role == 'assistant' else '#cccccc'};"
        )

        content_label = QLabel(message.content)
        content_label.setWordWrap(True)
        content_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.layout.addWidget(role_label)
        self.layout.addWidget(content_label)
        self.layout.setContentsMargins(10, 5, 10, 5)


class MessageView(QScrollArea):
    message_clicked = pyqtSignal(Message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.layout = QVBoxLayout(self.container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout.setSpacing(10)

        self.setWidget(self.container)
        self._messages = []

    def add_message(self, message: Message):
        msg_widget = MessageWidget(message, self)
        self.layout.addWidget(msg_widget)
        self._messages.append(message)

        # Scroll to bottom
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def clear_messages(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._messages.clear()

    def get_messages(self) -> list[Message]:
        return self._messages.copy()
