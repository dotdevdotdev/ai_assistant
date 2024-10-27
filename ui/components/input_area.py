from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
    QPushButton,
    QLabel,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent


class InputArea(QWidget):
    message_submitted = pyqtSignal(str)
    recording_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Text input
        self.text_edit = QTextEdit()
        self.text_edit.setPlaceholderText("Type your message here...")
        self.text_edit.setMaximumHeight(100)
        self.text_edit.textChanged.connect(self._on_text_changed)

        # Buttons layout
        button_layout = QHBoxLayout()

        self.record_button = QPushButton("🎤")
        self.record_button.setCheckable(True)
        self.record_button.clicked.connect(self._on_record_clicked)

        self.send_button = QPushButton("Send")
        self.send_button.setEnabled(False)
        self.send_button.clicked.connect(self._on_send_clicked)

        button_layout.addWidget(self.record_button)
        button_layout.addStretch()
        button_layout.addWidget(self.send_button)

        layout.addWidget(self.text_edit)
        layout.addLayout(button_layout)

    def _on_text_changed(self):
        self.send_button.setEnabled(bool(self.text_edit.toPlainText().strip()))

    def _on_send_clicked(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            self.message_submitted.emit(text)
            self.text_edit.clear()

    def _on_record_clicked(self, checked: bool):
        self.recording_toggled.emit(checked)
        self.text_edit.setEnabled(not checked)

    def keyPressEvent(self, event: QKeyEvent):
        if (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.NoModifier
        ):
            self._on_send_clicked()
            event.accept()
        else:
            super().keyPressEvent(event)
