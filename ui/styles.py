from PyQt6.QtGui import QPalette, QColor
from typing import Dict


class AppTheme:
    def __init__(self, colors: Dict[str, str]):
        self.colors = colors

    def get_palette(self) -> QPalette:
        palette = QPalette()

        # Set background color
        bg_color = QColor(self.colors.get("background", "#000000"))
        palette.setColor(QPalette.ColorRole.Window, bg_color)
        palette.setColor(QPalette.ColorRole.Base, bg_color)

        # Set text color
        text_color = QColor(self.colors.get("text", "#39FF14"))
        palette.setColor(QPalette.ColorRole.WindowText, text_color)
        palette.setColor(QPalette.ColorRole.Text, text_color)

        # Set accent color for highlights and selections
        accent_color = QColor(self.colors.get("accent", "#39FF14"))
        palette.setColor(QPalette.ColorRole.Highlight, accent_color)
        palette.setColor(QPalette.ColorRole.HighlightedText, bg_color)

        return palette

    def get_stylesheet(self) -> str:
        return f"""
        QWidget {{
            background-color: {self.colors.get("background", "#000000")};
            color: {self.colors.get("text", "#39FF14")};
        }}
        
        QPushButton {{
            background-color: {self.colors.get("accent", "#39FF14")};
            color: {self.colors.get("background", "#000000")};
            border: none;
            padding: 5px;
            border-radius: 3px;
        }}
        
        QPushButton:hover {{
            background-color: {self.colors.get("text", "#39FF14")};
        }}
        
        QComboBox {{
            background-color: {self.colors.get("background", "#000000")};
            color: {self.colors.get("text", "#39FF14")};
            border: 1px solid {self.colors.get("accent", "#39FF14")};
            padding: 5px;
            border-radius: 3px;
        }}
        
        QTextEdit {{
            background-color: {self.colors.get("background", "#000000")};
            color: {self.colors.get("text", "#39FF14")};
            border: 1px solid {self.colors.get("accent", "#39FF14")};
            border-radius: 3px;
        }}
        """
