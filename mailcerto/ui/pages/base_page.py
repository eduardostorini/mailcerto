from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton, QStackedWidget
from PySide6.QtCore import Qt

class PlaceholderPage(QWidget):
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        self.title_label = QLabel(title)
        self.title_label.setObjectName("titleLabel")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.desc_label = QLabel(description)
        self.desc_label.setObjectName("descLabel")
        self.desc_label.setWordWrap(True)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.desc_label)
        layout.addStretch()
