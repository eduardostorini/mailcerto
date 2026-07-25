import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableView, QProgressBar, QSplitter, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from mailcerto.ui.models import DNSResultsModel
from mailcerto.checks.reputation.blacklist_check import DEFAULT_DNSBL_PROVIDERS, check_dnsbl_single
from mailcerto.core.models import CheckResult, CheckStatus

class BlacklistPage(QWidget):
    check_finished = Signal(object)
    all_checks_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks = []
        self._current_results = []
        self.last_analyzed_ip = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel("Blacklists & Reputação")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Consulte a reputação do endereço IP em listas públicas de bloqueio (DNSBL).")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Vertical)
        
        self.results_model = DNSResultsModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.results_model)
        
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.clicked.connect(self.on_row_selected)
        splitter.addWidget(self.table_view)

        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 10, 0, 0)
        
        self.details_title = QLabel("Detalhes do Bloqueio")
        self.details_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.details_text = QLabel("Selecione um registro na tabela para ver os detalhes técnicos brutos.")
        self.details_text.setWordWrap(True)
        self.details_text.setAlignment(Qt.AlignTop)
        
        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_text)
        details_layout.addStretch()
        
        splitter.addWidget(self.details_widget)
        splitter.setSizes([600, 150])

        layout.addWidget(splitter)
        
        self.check_finished.connect(self.on_check_finished)
        self.all_checks_finished.connect(self.on_all_checks_finished)

    def on_row_selected(self, index):
        if not index.isValid():
            return
        row = index.row()
        if 0 <= row < len(self._current_results):
            result = self._current_results[row]
            detail_content = f"<b>Blacklist:</b> {result.title}<br/>"
            detail_content += f"<b>Status:</b> {result.status.value.upper()}<br/>"
            detail_content += f"<b>Tempo:</b> {result.response_time_ms:.2f} ms<br/><br/>"
            detail_content += f"<b>Resultado:</b> {result.summary}<br/><br/>"
            if result.details:
                detail_content += f"<b>Detalhes Técnicos:</b><br/><pre>{result.details}</pre>"
            if result.recommendation:
                detail_content += f"<br/><b>Recomendação:</b><br/>{result.recommendation}"
            self.details_text.setText(detail_content)

    def start_blacklist_analysis(self, target: str):
        # Resolve target IP first
        self.cancel_analysis()
        self._current_results = []
        self.results_model.update_results([])
        self.details_text.setText("Verificando blacklists... Por favor, aguarde.")
        
        # Obter endereço IP de forma segura
        import ipaddress
        ip_to_check = ""
        try:
            ipaddress.ip_address(target)
            ip_to_check = target
        except ValueError:
            # Resolve DNS name to IP
            try:
                import socket
                ip_to_check = socket.gethostbyname(target)
            except Exception:
                self.details_text.setText("Erro: Alvo deve ser um IP válido ou domínio resolvível.")
                return

        if self.last_analyzed_ip == ip_to_check and self._current_results:
            return
            
        self.last_analyzed_ip = ip_to_check
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(DEFAULT_DNSBL_PROVIDERS))
        self.progress_bar.setValue(0)
        
        # Parallel DNSBL tasks
        for provider in DEFAULT_DNSBL_PROVIDERS:
            task = asyncio.create_task(self._run_single_dnsbl(ip_to_check, provider))
            self.active_tasks.append(task)

    async def _run_single_dnsbl(self, ip: str, provider: dict):
        try:
            result = await check_dnsbl_single(ip, provider["zone"], provider["name"])
            self.check_finished.emit(result)
        except Exception as e:
            self.check_finished.emit(CheckResult(
                check_id=f"dnsbl_err_{provider['name']}", category="Reputação",
                title=provider["name"], status=CheckStatus.ERROR, summary=str(e)
            ))

    @Slot(object)
    def on_check_finished(self, result: CheckResult):
        self._current_results.append(result)
        self.results_model.update_results(list(self._current_results))
        self.progress_bar.setValue(len(self._current_results))
        self.table_view.viewport().update()
        
        if len(self._current_results) >= self.progress_bar.maximum():
            self.all_checks_finished.emit()

    @Slot()
    def on_all_checks_finished(self):
        self.progress_bar.setVisible(False)
        self.active_tasks = []

    def cancel_analysis(self):
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        self.active_tasks = []
        self.progress_bar.setVisible(False)
