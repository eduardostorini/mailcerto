import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QStackedWidget, QFrame, QListWidget, QListWidgetItem, QLabel, QProgressBar, QStatusBar,
    QMessageBox, QCompleter
)
from PySide6.QtCore import Qt, Slot, QStringListModel, QSize
from PySide6.QtGui import QIcon
from mailcerto.core.normalization import detect_and_normalize_target
from mailcerto.ui.pages.base_page import PlaceholderPage
from mailcerto.ui.pages.dashboard_page import DashboardPage
from mailcerto.ui.pages.email_auth_page import EmailAuthPage
from mailcerto.ui.pages.smtp_page import SMTPPage
from mailcerto.ui.pages.tls_page import TLSPage
from mailcerto.ui.pages.blacklist_page import BlacklistPage
from mailcerto.ui.pages.http_page import HttpPage
from mailcerto.ui.pages.log_page import LogPage
from mailcerto.ui.pages.super_analysis_page import SuperAnalysisPage
from mailcerto.ui.pages.network_page import NetworkPage
from mailcerto.ui.pages.rdap_page import RdapPage
from mailcerto.ui.pages.ports_page import PortsPage
from mailcerto.ui.pages.ip_location_page import IPLocationPage
from mailcerto.ui.pages.single_dns_page import SingleDNSPage
from mailcerto.ui.pages.bimi_page import BIMIPage
from mailcerto.ui.pages.dnssec_page import DNSSECPage
from mailcerto.database.repositories import get_unique_targets, save_analysis
from mailcerto.reports.report_generator import ReportGenerator
from mailcerto.core.models import AnalysisResult
from datetime import datetime

class MainWindow(QMainWindow):
    MENU_ICON_MAP = {
        "Visão Geral": ("fa.chart-pie", "#0066CC"),
        "Super Análise": ("fa.bolt", "#0099E6"),
        "DNS - MX": ("fa.envelope", "#1e90ff"),
        "DNS - TXT": ("fa.align-left", "#4682B4"),
        "DNS - A": ("fa.globe", "#2F7FB3"),
        "DNS - AAAA": ("fa.globe", "#2F7FB3"),
        "DNS - NS": ("fa.server", "#3F8FC3"),
        "DNS - CNAME": ("fa.link", "#4F9FD3"),
        "DNS - SOA": ("fa.info-circle", "#5FAFE3"),
        "BIMI": ("fa.stamp", "#6f42c1"),
        "DNSSEC": ("fa.lock", "#28a745"),
        "Autenticação": ("fa.user-shield", "#dc3545"),
        "SMTP": ("fa.paper-plane", "#fd7e14"),
        "TLS & Certificados": ("fa.certificate", "#20c997"),
        "Blacklists": ("fa.ban", "#8B0000"),
        "HTTP & Segurança": ("fa.shield-alt", "#6610f2"),
        "Rede": ("fa.network-wired", "#17a2b8"),
        "Localização de IP": ("fa.map-marker-alt", "#ef4444"),
        "Portas (Scan)": ("fa.ethernet", "#343a40"),
        "WHOIS & RDAP": ("fa.id-card", "#6c757d"),
        "Log": ("fa.scroll", "#495057"),
        "Sobre": ("fa.question-circle", "#adb5bd"),
    }

    def __init__(self, application_icon: QIcon | None = None):
        super().__init__()
        self.setWindowTitle("MailCerto")

        self._application_icon = QIcon() if application_icon is None else application_icon
        if not self._application_icon.isNull():
            self.setWindowIcon(self._application_icon)
        else:
            # Fallback: try to load directly from resources
            icon_path = Path(__file__).parent.parent / "resources" / "icon.ico"
            if not icon_path.exists():
                icon_path = Path(__file__).parent.parent / "resources" / "icon.png"
            if not icon_path.exists():
                icon_path = Path(__file__).parent.parent / "resources" / "icon.svg"
            if icon_path.exists():
                loaded = QIcon(str(icon_path))
                if not loaded.isNull():
                    self.setWindowIcon(loaded)
                    self._application_icon = loaded

        self.resize(1440, 900)
        self.setMinimumSize(1100, 700)

        self.current_target = ""
        self.completer_model = QStringListModel()
        self.current_results = []
        self.report_generator = ReportGenerator()
        self.init_ui()
        self.update_autocomplete_list()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # 1. Sidebar (Recolhível)
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFrameShape(QFrame.StyledPanel)
        self.sidebar.setFixedWidth(240)
        sidebar_layout = QVBoxLayout(self.sidebar)

        # Logotipo / Nome
        logo_label = QLabel("MailCerto")
        logo_label.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px 0;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)

        # Menu List - Quebrando DNS em submenus individuais
        self.menu_list = QListWidget()
        self.menu_list.setObjectName("menuList")

        self.menu_items = [
            "Visão Geral",
            "Super Análise",
            "DNS - MX",
            "DNS - TXT",
            "DNS - A",
            "DNS - AAAA",
            "DNS - NS",
            "DNS - CNAME",
            "DNS - SOA",
            "BIMI",
            "DNSSEC",
            "Autenticação",
            "SMTP",
            "TLS & Certificados",
            "Blacklists",
            "HTTP & Segurança",
            "Rede",
            "Localização de IP",
            "Portas (Scan)",
            "WHOIS & RDAP",
            "Log",
            "Sobre"
        ]
        self._populate_menu_items(self.menu_items)
        self.menu_list.setCurrentRow(0)
        self.menu_list.currentRowChanged.connect(self.on_menu_changed)
        sidebar_layout.addWidget(self.menu_list)

        # Sidebar collapse button
        self.btn_collapse = QPushButton("Recolher Menu")
        self.btn_collapse.clicked.connect(self.toggle_sidebar)
        sidebar_layout.addWidget(self.btn_collapse)

        main_layout.addWidget(self.sidebar)

        # 2. Content Area container
        self.content_container = QFrame()
        self.content_container.setObjectName("contentArea")
        content_layout = QVBoxLayout(self.content_container)

        # 2.1 Top bar
        top_bar = QFrame()
        top_bar.setFrameShape(QFrame.StyledPanel)
        top_layout = QHBoxLayout(top_bar)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Insira um domínio, IP ou URL (ex: sendlite.app)")
        self.search_input.textChanged.connect(self.on_target_input_changed)

        # Autocomplete Completer
        self.completer = QCompleter()
        self.completer.setModel(self.completer_model)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setFilterMode(Qt.MatchContains)
        self.search_input.setCompleter(self.completer)

        top_layout.addWidget(self.search_input)

        self.btn_analyze = QPushButton("Analisar")
        self.btn_analyze.clicked.connect(self.run_global_analysis)
        top_layout.addWidget(self.btn_analyze)

        self.btn_cancel = QPushButton("Parar")
        self.btn_cancel.clicked.connect(self.cancel_global_analysis)
        top_layout.addWidget(self.btn_cancel)

        self.btn_export_html = QPushButton("Exportar HTML")
        self.btn_export_html.clicked.connect(self.export_html_report)
        top_layout.addWidget(self.btn_export_html)

        self.btn_export_pdf = QPushButton("Exportar PDF")
        self.btn_export_pdf.clicked.connect(self.export_pdf_report)
        top_layout.addWidget(self.btn_export_pdf)

        # Apply icons to topbar buttons (best-effort using QtAwesome)
        self._apply_action_button_icons()

        content_layout.addWidget(top_bar)

        # 2.2 Stacked Pages widget
        self.pages_stack = QStackedWidget()

        # Initialize specific functional pages
        self.dashboard_page = DashboardPage()
        self.super_analysis_page = SuperAnalysisPage()

        # Submenus de DNS
        self.dns_mx_page = SingleDNSPage("MX", "Servidores de E-mail", "Lista os servidores MX responsáveis por receber e-mails pelo domínio.")
        self.dns_txt_page = SingleDNSPage("TXT", "Registros de Texto", "Lista strings de texto associadas ao domínio, usadas para verificação de propriedade.")
        self.dns_a_page = SingleDNSPage("A", "Apontamento IPv4", "Mapeia o domínio para um ou mais endereços IPv4 físicos.")
        self.dns_aaaa_page = SingleDNSPage("AAAA", "Apontamento IPv6", "Mapeia o domínio para um ou mais endereços IPv6 físicos.")
        self.dns_ns_page = SingleDNSPage("NS", "Servidores de Nomes", "Determina quais servidores DNS respondem oficialmente pelo domínio.")
        self.dns_cname_page = SingleDNSPage("CNAME", "Apelidos (Aliases)", "Mapeia um nome alternativo para o domínio principal ou canônico.")
        self.dns_soa_page = SingleDNSPage("SOA", "Início de Autoridade", "Contém informações administrativas cruciais da zona DNS (TTL, serial, refreshes).")

        self.bimi_page = BIMIPage()
        self.dnssec_page = DNSSECPage()

        self.email_auth_page = EmailAuthPage()
        self.smtp_page = SMTPPage()
        self.tls_page = TLSPage()
        self.blacklist_page = BlacklistPage()
        self.http_page = HttpPage()
        self.network_page = NetworkPage()
        self.ip_location_page = IPLocationPage()
        self.ports_page = PortsPage()
        self.rdap_page = RdapPage()
        self.log_page = LogPage()

        # Placeholders and real pages stacked
        self.pages_stack.addWidget(self.dashboard_page)         # index 0  - Visão Geral
        self.pages_stack.addWidget(self.super_analysis_page)     # index 1  - Super Análise
        self.pages_stack.addWidget(self.dns_mx_page)             # index 2  - DNS MX
        self.pages_stack.addWidget(self.dns_txt_page)            # index 3  - DNS TXT
        self.pages_stack.addWidget(self.dns_a_page)              # index 4  - DNS A
        self.pages_stack.addWidget(self.dns_aaaa_page)           # index 5  - DNS AAAA
        self.pages_stack.addWidget(self.dns_ns_page)             # index 6  - DNS NS
        self.pages_stack.addWidget(self.dns_cname_page)          # index 7  - DNS CNAME
        self.pages_stack.addWidget(self.dns_soa_page)            # index 8  - DNS SOA
        self.pages_stack.addWidget(self.bimi_page)               # index 9  - BIMI
        self.pages_stack.addWidget(self.dnssec_page)             # index 10 - DNSSEC
        self.pages_stack.addWidget(self.email_auth_page)         # index 11 - Autenticação
        self.pages_stack.addWidget(self.smtp_page)               # index 12 - SMTP
        self.pages_stack.addWidget(self.tls_page)                # index 13 - TLS & Certificados
        self.pages_stack.addWidget(self.blacklist_page)          # index 14 - Blacklists
        self.pages_stack.addWidget(self.http_page)               # index 15 - HTTP & Segurança
        self.pages_stack.addWidget(self.network_page)            # index 16 - Rede
        self.pages_stack.addWidget(self.ip_location_page)        # index 17 - Localização de IP
        self.pages_stack.addWidget(self.ports_page)              # index 18 - Portas (Scan)
        self.pages_stack.addWidget(self.rdap_page)               # index 19 - WHOIS & RDAP
        self.pages_stack.addWidget(self.log_page)                # index 20 - Log
        self.pages_stack.addWidget(PlaceholderPage("Sobre MailCerto", "MailCerto v1.0.0. Licença Apache 2.0.")) # index 21 - Sobre

        content_layout.addWidget(self.pages_stack)
        main_layout.addWidget(self.content_container)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Versão do aplicativo no rodapé
        self.version_label = QLabel("v1.0.0 ")
        self.status_bar.addPermanentWidget(self.version_label)
        self.status_bar.showMessage("Pronto")

    def toggle_sidebar(self):
        if self.sidebar.width() > 80:
            self.sidebar.setFixedWidth(80)
            self.btn_collapse.setText("Expandir")
        else:
            self.sidebar.setFixedWidth(240)
            self.btn_collapse.setText("Recolher Menu")

    def on_target_input_changed(self, text):
        cleaned = text.strip()
        normalized, target_type = detect_and_normalize_target(cleaned)
        if target_type != "invalid":
            self.current_target = normalized
        else:
            self.current_target = ""

    def on_menu_changed(self, row):
        self.pages_stack.setCurrentIndex(row)
        # Se entrar na aba de logs (Index 20), atualiza a lista automaticamente
        if row == 20:
            self.log_page.load_logs()

        # Se não há target em cache mas há texto no input, atualiza
        if not self.current_target and self.search_input.text().strip():
            normalized, target_type = detect_and_normalize_target(self.search_input.text().strip())
            if target_type != "invalid":
                self.current_target = normalized

        # Só dispara análise se houver um target válido em cache
        if self.current_target:
            self.trigger_page_analysis(row)

    def trigger_page_analysis(self, page_index):
        if not self.current_target:
            self.status_bar.showMessage("Aviso: Nenhum domínio em cache para analisar.")
            return

        clean_domain = self.current_target.replace("https://", "").replace("http://", "").split("/")[0].strip()
        if not clean_domain:
            return

        if page_index == 1:  # Super Análise Page
            self.status_bar.showMessage(f"Super Análise paralela iniciada para: {clean_domain}")
            try:
                self.super_analysis_page.start_super_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro na Super Análise: {str(e)}")
        elif page_index == 2:  # DNS MX
            self.status_bar.showMessage(f"Consultando registros MX para: {clean_domain}")
            self.dns_mx_page.start_dns_analysis(clean_domain)
        elif page_index == 3:  # DNS TXT
            self.status_bar.showMessage(f"Consultando registros TXT para: {clean_domain}")
            self.dns_txt_page.start_dns_analysis(clean_domain)
        elif page_index == 4:  # DNS A
            self.status_bar.showMessage(f"Consultando registros A para: {clean_domain}")
            self.dns_a_page.start_dns_analysis(clean_domain)
        elif page_index == 5:  # DNS AAAA
            self.status_bar.showMessage(f"Consultando registros AAAA para: {clean_domain}")
            self.dns_aaaa_page.start_dns_analysis(clean_domain)
        elif page_index == 6:  # DNS NS
            self.status_bar.showMessage(f"Consultando registros NS para: {clean_domain}")
            self.dns_ns_page.start_dns_analysis(clean_domain)
        elif page_index == 7:  # DNS CNAME
            self.status_bar.showMessage(f"Consultando registros CNAME para: {clean_domain}")
            self.dns_cname_page.start_dns_analysis(clean_domain)
        elif page_index == 8:  # DNS SOA
            self.status_bar.showMessage(f"Consultando registros SOA para: {clean_domain}")
            self.dns_soa_page.start_dns_analysis(clean_domain)
        elif page_index == 9:  # BIMI Page
            self.status_bar.showMessage(f"Consultando registros BIMI para: {clean_domain}")
            try:
                self.bimi_page.start_bimi_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 10:  # DNSSEC Page
            self.status_bar.showMessage(f"Consultando DNSSEC para: {clean_domain}")
            try:
                self.dnssec_page.start_dnssec_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 11:  # Autenticação Page (SPF, DMARC)
            self.status_bar.showMessage(f"Análise de Autenticação iniciada para: {clean_domain}")
            try:
                self.email_auth_page.start_auth_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 12:  # SMTP Page
            self.status_bar.showMessage(f"Análise SMTP iniciada para: {clean_domain}")
            try:
                self.smtp_page.start_smtp_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 13:  # TLS Page
            self.status_bar.showMessage(f"Análise TLS iniciada para: {clean_domain}")
            try:
                self.tls_page.start_tls_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 14:  # Blacklist Page
            self.status_bar.showMessage(f"Análise de Blacklist iniciada para: {clean_domain}")
            try:
                self.blacklist_page.start_blacklist_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 15:  # HTTP & Segurança Page
            self.status_bar.showMessage(f"Análise HTTP/Segurança iniciada para: {clean_domain}")
            try:
                self.http_page.start_http_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 16:  # Rede Page
            self.status_bar.showMessage(f"Análise de Rede iniciada para: {clean_domain}")
            try:
                self.network_page.start_network_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 17:  # Localização de IP Page
            self.status_bar.showMessage(f"Consultando localização de IP para: {clean_domain}")
            try:
                self.ip_location_page.start_location_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")
        elif page_index == 18:  # Portas (Scan) Page
            self.status_bar.showMessage(f"Escaneando portas do host: {clean_domain}")
            try:
                self.ports_page.start_ports_scan(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar escaneamento: {str(e)}")
        elif page_index == 19:  # RDAP Page
            self.status_bar.showMessage(f"Consulta RDAP iniciada para: {clean_domain}")
            try:
                self.rdap_page.start_rdap_analysis(clean_domain)
            except Exception as e:
                self.status_bar.showMessage(f"Erro ao iniciar análise: {str(e)}")

    def update_autocomplete_list(self):
        targets = get_unique_targets()
        self.completer_model.setStringList(targets)

    def run_global_analysis(self):
        target = self.search_input.text().strip()
        if not target:
            QMessageBox.warning(self, "Aviso", "Por favor, insira um alvo válido.")
            self.status_bar.showMessage("Erro: Entrada vazia.")
            return

        normalized, target_type = detect_and_normalize_target(target)
        if target_type == "invalid":
            QMessageBox.critical(self, "Erro", "Tipo de alvo inválido.")
            self.status_bar.showMessage(f"Erro: Alvo '{target}' inválido.")
            return

        self.current_target = normalized
        self.status_bar.showMessage(f"Analisando {normalized} ({target_type.upper()})...")

        # Salva o histórico de consulta no SQLite para popular o autocomplete e visão geral
        try:
            res = AnalysisResult(
                target=normalized,
                target_type=target_type,
                started_at=datetime.utcnow(),
                finished_at=datetime.utcnow()
            )
            save_analysis(res)
            self.update_autocomplete_list()
            if hasattr(self, 'dashboard_page'):
                self.dashboard_page.refresh_history()
        except Exception as e:
            print(f"[DATABASE] Falha ao registrar histórico: {str(e)}")

        current_idx = self.pages_stack.currentIndex()
        if current_idx == 0:
            self.menu_list.setCurrentRow(2)
        else:
            self.trigger_page_analysis(current_idx)

    def cancel_global_analysis(self):
        self.dns_mx_page.cancel_analysis()
        self.dns_txt_page.cancel_analysis()
        self.dns_a_page.cancel_analysis()
        self.dns_aaaa_page.cancel_analysis()
        self.dns_ns_page.cancel_analysis()
        self.dns_cname_page.cancel_analysis()
        self.dns_soa_page.cancel_analysis()
        self.bimi_page.cancel_analysis()
        self.dnssec_page.cancel_analysis()
        self.ip_location_page.cancel_analysis()
        self.super_analysis_page.cancel_analysis()
        self.status_bar.showMessage("Análise cancelada pelo usuário.")

    def _collect_all_results(self) -> list:
        """Collect CheckResult instances from all analysis pages, deduplicated by check_id."""
        seen_ids = set()
        collected = []

        result_pages = [
            self.super_analysis_page,
            self.dns_mx_page,
            self.dns_txt_page,
            self.dns_a_page,
            self.dns_aaaa_page,
            self.dns_ns_page,
            self.dns_cname_page,
            self.dns_soa_page,
            self.bimi_page,
            self.dnssec_page,
            self.email_auth_page,
            self.smtp_page,
            self.tls_page,
            self.blacklist_page,
            self.http_page,
            self.network_page,
            self.ip_location_page,
            self.ports_page,
            self.rdap_page,
        ]

        for page in result_pages:
            page_results = getattr(page, "_current_results", [])
            for result in page_results:
                rid = getattr(result, "check_id", id(result))
                if rid not in seen_ids:
                    seen_ids.add(rid)
                    collected.append(result)

        if not collected:
            collected = list(self.current_results)
        return collected

    def export_html_report(self):
        results = self._collect_all_results()
        if not self.current_target or not results:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar. Execute uma análise primeiro.")
            return
        
        try:
            from PySide6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Salvar Relatório HTML", 
                f"mailcerto_report_{self.current_target}.html",
                "HTML Files (*.html)"
            )
            
            if filename:
                output_path = self.report_generator.generate_html_report(
                    self.current_target, 
                    results, 
                    filename
                )
                QMessageBox.information(self, "Sucesso", f"Relatório HTML salvo em:\n{output_path}")
                self.status_bar.showMessage(f"Relatório HTML exportado: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório HTML:\n{str(e)}")

    def export_pdf_report(self):
        results = self._collect_all_results()
        if not self.current_target or not results:
            QMessageBox.warning(self, "Aviso", "Não há dados para exportar. Execute uma análise primeiro.")
            return
        
        try:
            from PySide6.QtWidgets import QFileDialog
            filename, _ = QFileDialog.getSaveFileName(
                self, "Salvar Relatório PDF", 
                f"mailcerto_report_{self.current_target}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if filename:
                output_path = self.report_generator.generate_pdf_report(
                    self.current_target, 
                    results, 
                    filename
                )
                QMessageBox.information(self, "Sucesso", f"Relatório PDF salvo em:\n{output_path}")
                self.status_bar.showMessage(f"Relatório PDF exportado: {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao exportar relatório PDF:\n{str(e)}")

    def _get_qta_icon(self, name: str, color: str = "#333333", size: int = 18) -> QIcon:
        """Return a QIcon from QtAwesome by name, or an empty QIcon if unavailable.
        Swallows import/render errors so missing qtawesome is not fatal."""
        try:
            import qtawesome as qta
            opts = {"color": color, "scale_factor": 1.0}
            icon = qta.icon(name, **opts)
            if not icon.isNull():
                return icon
        except Exception:
            pass
        return QIcon()

    def _populate_menu_items(self, items: list[str]):
        self.menu_list.clear()
        default_icon_size = QSize(20, 20)
        self.menu_list.setIconSize(default_icon_size)
        for label in items:
            item = QListWidgetItem(label)
            icon_info = self.MENU_ICON_MAP.get(label)
            if icon_info:
                icon_name, color = icon_info
                icon = self._get_qta_icon(icon_name, color, 18)
                if not icon.isNull():
                    item.setIcon(icon)
            self.menu_list.addItem(item)
        # When sidebar is collapsed, keep icons visible and hide text by using
        # a stylesheet-friendly minimum size; text will naturally elide.
        try:
            self.menu_list.setSpacing(4)
        except Exception:
            pass

    def _apply_action_button_icons(self):
        button_configs = [
            (self.btn_analyze, "fa.play", "#107c10"),
            (self.btn_cancel, "fa.stop", "#a4262c"),
            (self.btn_export_html, "fa.code", "#0078d4"),
            (self.btn_export_pdf, "fa.file-pdf-o", "#b00020"),
            (self.btn_collapse, "fa.bars", "#555555"),
        ]
        for button, icon_name, color in button_configs:
            try:
                icon = self._get_qta_icon(icon_name, color, 14)
                if not icon.isNull():
                    button.setIcon(icon)
            except Exception:
                pass
