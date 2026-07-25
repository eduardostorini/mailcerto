import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit, QLabel, QPushButton, QSplitter
)
from PySide6.QtCore import Qt
from mailcerto.database.repositories import get_recent_history

class LogPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.history_records = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        title = QLabel("Registro de Logs e Histórico")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Visualize todas as buscas realizadas anteriormente e os respectivos detalhes técnicos de seus resultados.")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        # Toolbar to refresh / clear
        btn_layout = QHBoxLayout()
        self.btn_refresh = QPushButton("Atualizar Logs")
        self.btn_refresh.clicked.connect(self.load_logs)
        btn_layout.addWidget(self.btn_refresh)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Splitter to display list of queries on the left, and full details on the right
        splitter = QSplitter(Qt.Horizontal)

        # List widget of queries
        self.log_list = QListWidget()
        self.log_list.currentRowChanged.connect(self.on_log_selected)
        splitter.addWidget(self.log_list)

        # Rich text detail viewer
        self.log_details = QTextEdit()
        self.log_details.setReadOnly(True)
        splitter.addWidget(self.log_details)

        splitter.setSizes([350, 650])
        layout.addWidget(splitter)

    def load_logs(self):
        self.log_list.clear()
        self.log_details.clear()
        self.history_records = get_recent_history(100) # Load up to 100 recent searches
        
        if not self.history_records:
            self.log_list.addItem("Nenhum log de consulta registrado ainda.")
            return

        for record in self.history_records:
            date_str = record["started_at"].strftime("%d/%m/%Y %H:%M:%S") if record["started_at"] else "N/A"
            item_text = f"{record['target']} ({record['target_type'].upper()}) - {date_str}"
            self.log_list.addItem(item_text)

    def on_log_selected(self, index):
        if index < 0 or index >= len(self.history_records):
            return
        
        record = self.history_records[index]
        date_str = record["started_at"].strftime("%d/%m/%Y %H:%M:%S") if record["started_at"] else "N/A"
        
        detail_content = f"<h2>Detalhes do Log #{record['id']}</h2>"
        detail_content += f"<b>Alvo Consultado:</b> {record['target']}<br/>"
        detail_content += f"<b>Tipo de Alvo:</b> {record['target_type'].upper()}<br/>"
        detail_content += f"<b>Data/Hora da Consulta:</b> {date_str}<br/>"
        detail_content += f"<b>Tempo de Execução:</b> {record['duration_ms']} ms<br/>"
        detail_content += f"<b>Pontuação Geral:</b> {record['score_general']}/100<br/>"
        
        detail_content += "<h3>Resultados das Verificações Executadas:</h3>"
        
        # Load results JSON if populated
        if record.get("results_json"):
            try:
                checks = json.loads(record["results_json"])
                if not checks:
                    detail_content += "<p>Nenhuma verificação individual foi executada ou registrada nesta sessão.</p>"
                for idx, check in enumerate(checks, 1):
                    status_color = "#22C55E" # green
                    if check["status"] in ["error", "critical"]:
                        status_color = "#EF4444" # red
                    elif check["status"] in ["warning"]:
                        status_color = "#F59E0B" # yellow
                    elif check["status"] in ["info"]:
                        status_color = "#3B82F6" # blue
                        
                    detail_content += f"<div style='border: 1px solid #CCCCCC; border-radius: 4px; padding: 10px; margin-bottom: 10px;'>"
                    detail_content += f"<b>{idx}. {check['title']}</b> - <span style='color: {status_color}; font-weight: bold;'>{check['status'].upper()}</span><br/>"
                    detail_content += f"<b>Sumário:</b> {check['summary']}<br/>"
                    if check.get("details"):
                        detail_content += f"<b>Detalhes Técnicos:</b><br/><pre style='background: #FAFAFA; padding: 5px; border-radius: 3px;'>{check['details']}</pre>"
                    if check.get("recommendation"):
                        detail_content += f"<b>Recomendação:</b> {check['recommendation']}<br/>"
                    detail_content += "</div>"
            except Exception as e:
                detail_content += f"<p style='color: red;'>Erro ao ler dados das verificações: {str(e)}</p>"
        else:
            # Fallback mock/empty display
            detail_content += "<p>Aguardando dados adicionais de verificação detalhada.</p>"

        self.log_details.setHtml(detail_content)
