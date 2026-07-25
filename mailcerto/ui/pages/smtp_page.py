import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTableView, QProgressBar, QSplitter, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from mailcerto.ui.models import DNSResultsModel
from mailcerto.checks.smtp.smtp_check import perform_smtp_check
from mailcerto.core.models import CheckResult, CheckStatus

class SMTPPage(QWidget):
    check_finished = Signal(object)
    all_checks_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks = []
        self._current_results = []
        self.last_analyzed_domain = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        title = QLabel("Servidor SMTP")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Teste a conectividade e banner SMTP na porta 25 do servidor MX.")
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
        
        self.details_title = QLabel("Detalhes do SMTP")
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
            detail_content = f"<b>Título:</b> {result.title}<br/>"
            detail_content += f"<b>Status:</b> {result.status.value.upper()}<br/>"
            detail_content += f"<b>Tempo de Resposta:</b> {result.response_time_ms:.2f} ms<br/><br/>"
            detail_content += f"<b>Sumário:</b> {result.summary}<br/><br/>"
            if result.details:
                detail_content += f"<b>Sessão SMTP / Detalhes:</b><br/><pre>{result.details}</pre>"
            if result.recommendation:
                detail_content += f"<br/><b>Recomendação:</b><br/>{result.recommendation}"
            self.details_text.setText(detail_content)

    def start_smtp_analysis(self, domain: str):
        if self.last_analyzed_domain == domain and self._current_results:
            return

        self.cancel_analysis()
        self._current_results = []
        self.results_model.update_results([])
        self.last_analyzed_domain = domain
        self.details_text.setText("Conectando ao servidor MX... Por favor, aguarde.")
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)
        
        task = asyncio.create_task(self._run_smtp_check(domain))
        self.active_tasks.append(task)

    async def _run_smtp_check(self, domain: str):
        try:
            results = await perform_smtp_check(domain)
            for r in results:
                self.check_finished.emit(r)
        except Exception as e:
            self.check_finished.emit(CheckResult(
                check_id="smtp_err", category="SMTP", title="SMTP",
                status=CheckStatus.ERROR, summary=str(e)
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
