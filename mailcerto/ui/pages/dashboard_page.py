from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PySide6.QtCore import Qt
from mailcerto.database.repositories import get_recent_history

class DashboardPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Title
        title = QLabel("Visão Geral")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Bem-vindo ao MailCerto. Insira um alvo no topo ou inicie uma verificação.")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        # Dashboard metrics grid
        self.metrics_grid = QGridLayout()
        self.metrics_grid.setSpacing(10)
        
        # Add summary metric cards
        self.total_checks_card = self.create_card("Total de Verificações", "0")
        self.issues_card = self.create_card("Problemas Críticos", "0")
        self.certificates_card = self.create_card("Certificados expirando", "N/A")
        
        self.metrics_grid.addWidget(self.total_checks_card, 0, 0)
        self.metrics_grid.addWidget(self.issues_card, 0, 1)
        self.metrics_grid.addWidget(self.certificates_card, 0, 2)
        
        layout.addLayout(self.metrics_grid)

        # Recent activities / History area
        history_title = QLabel("Histórico de Análises Recentes")
        history_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(history_title)

        self.history_frame = QFrame()
        self.history_frame.setObjectName("contentArea")
        self.history_frame.setFrameShape(QFrame.StyledPanel)
        self.history_layout = QVBoxLayout(self.history_frame)
        self.history_layout.setContentsMargins(10, 10, 10, 10)
        
        self.no_history_label = QLabel("Nenhum histórico encontrado ainda. Execute a sua primeira análise!")
        self.history_layout.addWidget(self.no_history_label)
        layout.addWidget(self.history_frame)

        layout.addStretch()
        
    def create_card(self, title: str, value: str) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.StyledPanel)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(10, 10, 10, 10)
        
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("font-size: 11px;")
        
        value_lbl = QLabel(value)
        value_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        card_layout.addWidget(title_lbl)
        card_layout.addWidget(value_lbl)
        return card

    def refresh_history(self):
        # Clean history items
        for i in reversed(range(self.history_layout.count())):
            widget = self.history_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                
        history = get_recent_history(5)
        if not history:
            self.history_layout.addWidget(QLabel("Nenhum histórico encontrado ainda. Execute a sua primeira análise!"))
            return
            
        for h in history:
            item_lbl = QLabel(f"• {h['target']} ({h['target_type'].upper()}) - Nota: {h['score_general']}/100 - {h['started_at'].strftime('%d/%m/%Y %H:%M')}")
            self.history_layout.addWidget(item_lbl)
            
        # Update metrics summary
        self.total_checks_card.findChildren(QLabel)[1].setText(str(len(history)))
