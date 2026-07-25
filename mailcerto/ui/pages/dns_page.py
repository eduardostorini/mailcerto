import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableView, QProgressBar, QCheckBox, QSplitter, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from mailcerto.ui.models import DNSResultsModel
from mailcerto.checks.dns.dns_check import perform_dns_check
from mailcerto.core.models import CheckResult, CheckStatus

class DNSPage(QWidget):
    check_finished = Signal(object)
    all_checks_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks = []
        self._current_results = []
        self.last_analyzed_domain = ""  # Cache do último domínio analisado nesta página
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Header
        title = QLabel("Verificações DNS")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        desc = QLabel("Consulte e analise os principais registros DNS de um domínio.")
        desc.setObjectName("descLabel")
        layout.addWidget(desc)

        # DNS Options checkboxes
        opts_layout = QHBoxLayout()
        self.chk_a = QCheckBox("A")
        self.chk_aaaa = QCheckBox("AAAA")
        self.chk_mx = QCheckBox("MX")
        self.chk_ns = QCheckBox("NS")
        self.chk_txt = QCheckBox("TXT")
        self.chk_cname = QCheckBox("CNAME")
        self.chk_soa = QCheckBox("SOA")
        
        for chk in [self.chk_a, self.chk_aaaa, self.chk_mx, self.chk_ns, self.chk_txt, self.chk_cname, self.chk_soa]:
            chk.setChecked(True)
            opts_layout.addWidget(chk)
        
        layout.addLayout(opts_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Splitter set to vertical so the table occupies the maximum width possible
        splitter = QSplitter(Qt.Vertical)
        
        # Results table
        self.results_model = DNSResultsModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.results_model)
        
        # Make columns stretch and resize to fill all available width
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        
        self.table_view.clicked.connect(self.on_row_selected)
        splitter.addWidget(self.table_view)

        # Technical details bottom view (under the table, taking less space)
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 10, 0, 0)
        
        self.details_title = QLabel("Detalhes do Registro")
        self.details_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.details_text = QLabel("Selecione um registro na tabela para ver os detalhes técnicos brutos.")
        self.details_text.setWordWrap(True)
        self.details_text.setAlignment(Qt.AlignTop)
        
        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_text)
        details_layout.addStretch()
        
        splitter.addWidget(self.details_widget)
        
        # Table occupies 80% and Details occupies 20% of the vertical space
        splitter.setSizes([600, 150])

        layout.addWidget(splitter)
        
        # Connect signals
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
                detail_content += f"<b>Detalhes Técnicos:</b><br/><pre>{result.details}</pre>"
            if result.recommendation:
                detail_content += f"<br/><b>Recomendação:</b><br/>{result.recommendation}"
            self.details_text.setText(detail_content)

    def start_dns_analysis(self, domain: str):
        # Evitar re-analisar se já foi analisado com sucesso
        if self.last_analyzed_domain == domain and self._current_results:
            return

        self.cancel_analysis()
        self._current_results = []
        self.results_model.update_results([])
        self.last_analyzed_domain = domain
        self.details_text.setText("Buscando registros DNS... Por favor, aguarde.")
        
        record_types = []
        if self.chk_a.isChecked(): record_types.append("A")
        if self.chk_aaaa.isChecked(): record_types.append("AAAA")
        if self.chk_mx.isChecked(): record_types.append("MX")
        if self.chk_ns.isChecked(): record_types.append("NS")
        if self.chk_txt.isChecked(): record_types.append("TXT")
        if self.chk_cname.isChecked(): record_types.append("CNAME")
        if self.chk_soa.isChecked(): record_types.append("SOA")
        
        if not record_types:
            self.details_text.setText("Erro: Nenhum tipo de registro DNS selecionado para consulta.")
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(record_types))
        self.progress_bar.setValue(0)
        
        # Launch asyncio tasks
        for r_type in record_types:
            task = asyncio.create_task(self._run_single_dns_check(domain, r_type))
            self.active_tasks.append(task)
            
    async def _run_single_dns_check(self, domain: str, r_type: str):
        try:
            result = await perform_dns_check(domain, r_type)
            self.check_finished.emit(result)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            err_result = CheckResult(
                check_id=f"dns_{r_type.lower()}",
                category="DNS",
                title=f"Registro DNS {r_type}",
                status=CheckStatus.ERROR,
                summary=f"Erro interno: {str(e)}",
                started_at=None
            )
            self.check_finished.emit(err_result)
            
    @Slot(object)
    def on_check_finished(self, result: CheckResult):
        self._current_results.append(result)
        self.results_model.update_results(list(self._current_results))
        self.progress_bar.setValue(len(self._current_results))
        
        # Force table update and resize columns
        self.table_view.viewport().update()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # Output status/errors to status bar
        window = self.window()
        if window and hasattr(window, 'status_bar'):
            if result.status in [CheckStatus.ERROR, CheckStatus.CRITICAL, CheckStatus.WARNING]:
                window.status_bar.showMessage(f"Erro em {result.title}: {result.summary}")
            else:
                window.status_bar.showMessage(f"Concluído: {result.title}")
        
        if len(self._current_results) >= self.progress_bar.maximum():
            self.all_checks_finished.emit()

    @Slot()
    def on_all_checks_finished(self):
        self.progress_bar.setVisible(False)
        self.active_tasks = []
        window = self.window()
        if window and hasattr(window, 'status_bar'):
            window.status_bar.showMessage(f"Análise DNS para '{self.last_analyzed_domain}' concluída.")

    def cancel_analysis(self):
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        self.active_tasks = []
        self.progress_bar.setVisible(False)
