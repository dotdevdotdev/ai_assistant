from PyQt6.QtGui import QColor, QPalette
from PyQt6.QtCore import Qt


class AppTheme:
    def __init__(self, dark_mode: bool = True):
        self.dark_mode = dark_mode
        self._init_colors()

    def _init_colors(self):
        if self.dark_mode:
            self.bg_primary = QColor("#1e1e1e")
            self.bg_secondary = QColor("#252526")
            self.text_primary = QColor("#ffffff")
            self.text_secondary = QColor("#cccccc")
            self.accent = QColor("#0078d4")
            self.error = QColor("#f85149")
            self.success = QColor("#4ac26b")
        else:
            self.bg_primary = QColor("#ffffff")
            self.bg_secondary = QColor("#f3f3f3")
            self.text_primary = QColor("#000000")
            self.text_secondary = QColor("#666666")
            self.accent = QColor("#0078d4")
            self.error = QColor("#d73a49")
            self.success = QColor("#28a745")

    def get_palette(self) -> QPalette:
        palette = QPalette()

        # Set window and widget background colors
        palette.setColor(QPalette.ColorRole.Window, self.bg_primary)
        palette.setColor(QPalette.ColorRole.Base, self.bg_secondary)

        # Set text colors
        palette.setColor(QPalette.ColorRole.WindowText, self.text_primary)
        palette.setColor(QPalette.ColorRole.Text, self.text_primary)
        palette.setColor(QPalette.ColorRole.PlaceholderText, self.text_secondary)

        # Set button colors
        palette.setColor(QPalette.ColorRole.Button, self.bg_secondary)
        palette.setColor(QPalette.ColorRole.ButtonText, self.text_primary)

        # Set highlight colors
        palette.setColor(QPalette.ColorRole.Highlight, self.accent)
        palette.setColor(QPalette.ColorRole.HighlightedText, self.text_primary)

        return palette

    def get_stylesheet(self) -> str:
        return f"""
            QMainWindow {{
                background-color: {self.bg_primary.name()};
            }}
            
            QWidget {{
                background-color: {self.bg_primary.name()};
                color: {self.text_primary.name()};
            }}
            
            QPushButton {{
                background-color: {self.bg_secondary.name()};
                border: 1px solid {self.accent.name()};
                border-radius: 4px;
                padding: 5px 15px;
                color: {self.text_primary.name()};
            }}
            
            QPushButton:hover {{
                background-color: {self.accent.name()};
                color: {self.text_primary.name()};
            }}
            
            QLineEdit, QTextEdit {{
                background-color: {self.bg_secondary.name()};
                border: 1px solid {self.bg_secondary.darker(120).name()};
                border-radius: 4px;
                padding: 5px;
                color: {self.text_primary.name()};
            }}
            
            QComboBox {{
                background-color: {self.bg_secondary.name()};
                border: 1px solid {self.bg_secondary.darker(120).name()};
                border-radius: 4px;
                padding: 5px;
                color: {self.text_primary.name()};
            }}
            
            QScrollBar:vertical {{
                border: none;
                background-color: {self.bg_secondary.name()};
                width: 10px;
                margin: 0px;
            }}
            
            QScrollBar::handle:vertical {{
                background-color: {self.accent.name()};
                border-radius: 5px;
                min-height: 20px;
            }}
            
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """
