import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QProgressBar, QSplitter, QTableView, QHeaderView
)
from PySide6.QtCore import Qt, Signal, Slot
from mailcerto.ui.models import IPLocationResultsModel
from mailcerto.checks.network.ip_location import check_ip_location
from mailcerto.core.models import CheckResult, CheckStatus


class IPLocationPage(QWidget):
    check_finished = Signal(object)
    all_checks_finished = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_tasks = []
        self._current_results = []
        self.last_analyzed_target = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # Title
        title = QLabel("Localização Geográfica de IP / Domínio")
        title.setObjectName("titleLabel")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "Consulte a localização geográfica de um endereço IP ou domínio. "
            "Domínios são convertidos para IP antes da consulta. "
            "Usa ipapi.co com fallback automático para ip-api.com em caso de limite de requisições."
        )
        desc.setObjectName("descLabel")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Input Section
        input_frame = QFrame()
        input_frame.setObjectName("inputSection")
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        input_layout.setSpacing(10)

        input_label = QLabel("IP ou Domínio:")
        input_label.setStyleSheet("font-weight: bold;")
        input_layout.addWidget(input_label)

        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Ex: google.com ou 8.8.8.8")
        self.target_input.returnPressed.connect(self.on_analyze_clicked)
        input_layout.addWidget(self.target_input)

        self.btn_analyze = QPushButton("Analisar Localização")
        self.btn_analyze.clicked.connect(self.on_analyze_clicked)
        self.btn_analyze.setMinimumWidth(150)
        input_layout.addWidget(self.btn_analyze)

        layout.addWidget(input_frame)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results area with splitter
        splitter = QSplitter(Qt.Vertical)

        # Results table
        self.results_model = IPLocationResultsModel()
        self.table_view = QTableView()
        self.table_view.setModel(self.results_model)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        vheader = self.table_view.verticalHeader()
        vheader.setDefaultAlignment(Qt.AlignCenter)
        self.table_view.clicked.connect(self.on_row_selected)
        splitter.addWidget(self.table_view)

        # Detailed results display
        self.details_widget = QWidget()
        details_layout = QVBoxLayout(self.details_widget)
        details_layout.setContentsMargins(0, 10, 0, 0)

        self.details_title = QLabel("Detalhes da Localização")
        self.details_title.setStyleSheet("font-size: 14px; font-weight: bold;")

        self.details_text = QLabel(
            "Insira um IP ou domínio e clique em 'Analisar Localização' para ver os detalhes."
        )
        self.details_text.setWordWrap(True)
        self.details_text.setAlignment(Qt.AlignTop)
        self.details_text.setStyleSheet(
            "background-color: rgba(0, 0, 0, 0.05); padding: 10px; border-radius: 5px;"
        )

        details_layout.addWidget(self.details_title)
        details_layout.addWidget(self.details_text)
        details_layout.addStretch()

        splitter.addWidget(self.details_widget)
        splitter.setSizes([400, 250])

        layout.addWidget(splitter)

        self.check_finished.connect(self.on_check_finished)
        self.all_checks_finished.connect(self.on_all_checks_finished)

    def on_analyze_clicked(self):
        target = self.target_input.text().strip()
        if not target:
            self.details_text.setText(
                "<span style='color: red;'>Por favor, insira um IP ou domínio.</span>"
            )
            return

        self.start_location_analysis(target)

    def start_location_analysis(self, target: str):
        """Inicia a análise de localização do IP/domínio"""
        if self.last_analyzed_target == target and self._current_results:
            return

        self.cancel_analysis()
        self._current_results = []
        self.results_model.update_results([])
        self.last_analyzed_target = target
        self.details_text.setText(
            f"<b>Analisando:</b> {target}<br/>"
            "Consultando localização (domínio → IP, depois API)... Por favor, aguarde."
        )

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(1)
        self.progress_bar.setValue(0)

        task = asyncio.create_task(self._run_location_check(target))
        self.active_tasks.append(task)

    async def _run_location_check(self, target: str):
        """Executa a verificação de localização de forma assíncrona"""
        try:
            results = await check_ip_location(target)
            self.progress_bar.setMaximum(len(results))
            for r in results:
                self.check_finished.emit(r)
        except Exception as e:
            self.check_finished.emit(CheckResult(
                check_id="loc_err", category="Localização", title="Localização Geográfica",
                status=CheckStatus.ERROR, summary=f"Erro ao analisar localização: {str(e)}"
            ))

    def on_row_selected(self, index):
        """Exibe os detalhes completos do resultado selecionado"""
        if not index.isValid():
            return

        row = index.row()
        if 0 <= row < len(self._current_results):
            result = self._current_results[row]

            # Criar HTML formatado com os detalhes
            html_content = f"""
            <div style='font-family: Arial, sans-serif;'>
                <div style='margin-bottom: 10px;'>
                    <b>Título:</b> {result.title}<br/>
                    <b>Status:</b> <span style='color: {"green" if result.status == CheckStatus.SUCCESS else "orange"};'>
                        {result.status.value.upper()}
                    </span><br/>
                    <b>Tempo de resposta:</b> {result.response_time_ms:.2f} ms
                </div>

                <div style='background-color: rgba(0, 100, 200, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px;'>
                    <b>Resultado:</b><br/>
                    {result.summary}
                </div>

                {f'<div style="background-color: rgba(50, 50, 50, 0.1); padding: 10px; border-radius: 5px; margin-bottom: 10px; font-family: monospace; white-space: pre-wrap;">'
                    f'<b>Detalhes Técnicos:</b><br/>{result.details}</div>' if result.details else ''}

                {f'<div style="background-color: rgba(0, 150, 0, 0.1); padding: 10px; border-radius: 5px;"><b>Recomendação:</b><br/>{result.recommendation}</div>' if result.recommendation else ''}
            </div>
            """

            self.details_text.setText(html_content)

    @Slot(object)
    def on_check_finished(self, result):
        """Chamado quando um check é concluído"""
        self._current_results.append(result)
        self.results_model.update_results(list(self._current_results))
        self.progress_bar.setValue(len(self._current_results))
        self.table_view.viewport().update()

        if len(self._current_results) >= self.progress_bar.maximum():
            self.all_checks_finished.emit()

    @Slot()
    def on_all_checks_finished(self):
        """Chamado quando todos os checks estão concluídos"""
        self.progress_bar.setVisible(False)
        self.active_tasks = []

    def cancel_analysis(self):
        """Cancela a análise em andamento"""
        for task in self.active_tasks:
            if not task.done():
                task.cancel()
        self.active_tasks = []
        self.progress_bar.setVisible(False)

    def cleanup(self):
        """Limpa recursos antes de fechar a página"""
        self.cancel_analysis()
