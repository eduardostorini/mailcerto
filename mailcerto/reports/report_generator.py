import os
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from mailcerto.core.models import CheckResult, CheckStatus

class ReportGenerator:
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        self.ensure_templates_exist()

    def ensure_templates_exist(self):
        """Create default templates if they don't exist"""
        if not self.template_dir.exists():
            self.template_dir.mkdir(parents=True)
        
        html_template = self.template_dir / "report.html"
        if not html_template.exists():
            self._create_html_template(html_template)

    def _create_html_template(self, template_path):
        template_content = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório MailCerto - {{ domain }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .header {
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        .header h1 {
            color: #007bff;
            margin: 0;
        }
        .header .meta {
            color: #666;
            margin-top: 10px;
        }
        .summary {
            background-color: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 30px;
        }
        .summary h2 {
            margin-top: 0;
            color: #333;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }
        .stat-box {
            background-color: white;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
            border-left: 4px solid #007bff;
        }
        .stat-box.success { border-left-color: #28a745; }
        .stat-box.warning { border-left-color: #ffc107; }
        .stat-box.error { border-left-color: #dc3545; }
        .stat-box.critical { border-left-color: #dc3545; }
        .stat-box.info { border-left-color: #17a2b8; }
        .stat-box.recommendation { border-left-color: #6f42c1; }
        .stat-box.skipped { border-left-color: #6c757d; }
        .stat-box.inconclusive { border-left-color: #6c757d; }
        .stat-box .number {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .stat-box .label {
            color: #666;
            font-size: 14px;
        }
        .section {
            margin-bottom: 30px;
        }
        .section h2 {
            color: #333;
            border-bottom: 2px solid #e9ecef;
            padding-bottom: 10px;
        }
        .check-item {
            background-color: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 5px;
            border-left: 4px solid #ccc;
        }
        .check-item.success { border-left-color: #28a745; }
        .check-item.warning { border-left-color: #ffc107; }
        .check-item.error { border-left-color: #dc3545; }
        .check-item.critical { border-left-color: #dc3545; }
        .check-item.info { border-left-color: #17a2b8; }
        .check-item.recommendation { border-left-color: #6f42c1; }
        .check-item.skipped { border-left-color: #6c757d; }
        .check-item.inconclusive { border-left-color: #6c757d; }
        .check-item .title {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        .check-item .status {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            margin-left: 10px;
        }
        .check-item.success .status { background-color: #d4edda; color: #155724; }
        .check-item.warning .status { background-color: #fff3cd; color: #856404; }
        .check-item.error .status { background-color: #f8d7da; color: #721c24; }
        .check-item.critical .status { background-color: #f8d7da; color: #721c24; }
        .check-item.info .status { background-color: #d1ecf1; color: #0c5460; }
        .check-item.recommendation .status { background-color: #e2d5f1; color: #4a2c7a; }
        .check-item.skipped .status { background-color: #e2e3e5; color: #383d41; }
        .check-item.inconclusive .status { background-color: #e2e3e5; color: #383d41; }
        .check-item .summary {
            color: #666;
            margin-top: 5px;
        }
        .check-item .details {
            margin-top: 10px;
            padding: 10px;
            background-color: white;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        .check-item .recommendation {
            margin-top: 10px;
            padding: 10px;
            background-color: #fff3cd;
            border-radius: 3px;
            font-size: 13px;
        }
        .footer {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Relatório de Análise MailCerto</h1>
            <div class="meta">
                <strong>Domínio:</strong> {{ domain }}<br>
                <strong>Data:</strong> {{ generated_at }}<br>
                <strong>Total de Verificações:</strong> {{ total_checks }}
            </div>
        </div>

        <div class="summary">
            <h2>Resumo Executivo</h2>
            <div class="stats">
                <div class="stat-box success">
                    <div class="number">{{ success_count }}</div>
                    <div class="label">Sucesso</div>
                </div>
                <div class="stat-box warning">
                    <div class="number">{{ warning_count }}</div>
                    <div class="label">Avisos</div>
                </div>
                <div class="stat-box error">
                    <div class="number">{{ error_count }}</div>
                    <div class="label">Erros</div>
                </div>
                <div class="stat-box critical">
                    <div class="number">{{ critical_count }}</div>
                    <div class="label">Críticos</div>
                </div>
            </div>
        </div>

        {% for category, checks in categorized_checks.items() %}
        <div class="section">
            <h2>{{ category }}</h2>
            {% for check in checks %}
            <div class="check-item {{ check.status.value }}">
                <div class="title">
                    {{ check.title }}
                    <span class="status">{{ check.status.value.upper() }}</span>
                </div>
                <div class="summary">{{ check.summary }}</div>
                {% if check.details %}
                <div class="details">{{ check.details }}</div>
                {% endif %}
                {% if check.recommendation %}
                <div class="recommendation"><strong>Recomendação:</strong> {{ check.recommendation }}</div>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        {% endfor %}

        <div class="footer">
            <p>Gerado por MailCerto - Ferramenta de Análise de Segurança de Domínios e E-mail</p>
            <p>{{ generated_at }}</p>
        </div>
    </div>
</body>
</html>"""
        template_path.write_text(template_content, encoding='utf-8')

    def generate_html_report(self, domain: str, results: list[CheckResult], output_path: str = None) -> str:
        """Generate HTML report from check results"""
        template = self.env.get_template("report.html")
        
        # Categorize results
        categorized = {}
        for result in results:
            category = result.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(result)
        
        # Count statuses
        success_count = sum(1 for r in results if r.status == CheckStatus.SUCCESS)
        warning_count = sum(1 for r in results if r.status == CheckStatus.WARNING)
        error_count = sum(1 for r in results if r.status == CheckStatus.ERROR)
        critical_count = sum(1 for r in results if r.status == CheckStatus.CRITICAL)
        
        html_content = template.render(
            domain=domain,
            generated_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            total_checks=len(results),
            success_count=success_count,
            warning_count=warning_count,
            error_count=error_count,
            critical_count=critical_count,
            categorized_checks=categorized
        )
        
        if output_path is None:
            output_path = f"mailcerto_report_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path

    def generate_pdf_report(self, domain: str, results: list[CheckResult], output_path: str = None) -> str:
        """Generate PDF report from check results"""
        if output_path is None:
            output_path = f"mailcerto_report_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        doc = SimpleDocTemplate(output_path, pagesize=A4,
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=18)
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#007bff'),
            spaceAfter=30
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12
        )
        
        story = []
        
        # Title
        story.append(Paragraph("Relatório de Análise MailCerto", title_style))
        story.append(Spacer(1, 12))
        
        # Metadata
        meta_data = [
            ['Domínio:', domain],
            ['Data:', datetime.now().strftime("%d/%m/%Y %H:%M:%S")],
            ['Total de Verificações:', str(len(results))]
        ]
        
        meta_table = Table(meta_data, colWidths=[2*inch, 4*inch])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f8f9fa')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(meta_table)
        story.append(Spacer(1, 24))
        
        # Summary statistics
        success_count = sum(1 for r in results if r.status == CheckStatus.SUCCESS)
        warning_count = sum(1 for r in results if r.status == CheckStatus.WARNING)
        error_count = sum(1 for r in results if r.status == CheckStatus.ERROR)
        critical_count = sum(1 for r in results if r.status == CheckStatus.CRITICAL)
        
        story.append(Paragraph("Resumo Executivo", heading_style))
        
        stats_data = [
            ['Sucesso', str(success_count), 'Avisos', str(warning_count)],
            ['Erros', str(error_count), 'Críticos', str(critical_count)]
        ]
        
        stats_table = Table(stats_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#d4edda')),
            ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#fff3cd')),
            ('BACKGROUND', (0, 1), (1, 1), colors.HexColor('#f8d7da')),
            ('BACKGROUND', (2, 1), (3, 1), colors.HexColor('#f8d7da')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 24))
        story.append(PageBreak())
        
        # Categorized results
        categorized = {}
        for result in results:
            category = result.category
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(result)
        
        for category, checks in categorized.items():
            story.append(Paragraph(category, heading_style))
            
            for check in checks:
                # Status color
                status_colors = {
                    CheckStatus.SUCCESS: colors.HexColor('#28a745'),
                    CheckStatus.WARNING: colors.HexColor('#ffc107'),
                    CheckStatus.ERROR: colors.HexColor('#dc3545'),
                    CheckStatus.CRITICAL: colors.HexColor('#dc3545'),
                    CheckStatus.INFO: colors.HexColor('#17a2b8'),
                    CheckStatus.RECOMMENDATION: colors.HexColor('#6f42c1'),
                    CheckStatus.SKIPPED: colors.HexColor('#6c757d'),
                    CheckStatus.INCONCLUSIVE: colors.HexColor('#6c757d'),
                }
                status_color = status_colors.get(check.status, colors.black)
                
                # Check title with status
                title_text = f"<b>{check.title}</b> - <font color='{status_color.hexval()}'>{check.status.value.upper()}</font>"
                story.append(Paragraph(title_text, styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Summary
                story.append(Paragraph(f"<i>{check.summary}</i>", styles['Normal']))
                story.append(Spacer(1, 6))
                
                # Details
                if check.details:
                    details_text = check.details.replace('\n', '<br/>')
                    story.append(Paragraph(details_text, styles['Code']))
                    story.append(Spacer(1, 6))
                
                # Recommendation
                if check.recommendation:
                    rec_text = f"<b>Recomendação:</b> {check.recommendation}"
                    story.append(Paragraph(rec_text, styles['Normal']))
                
                story.append(Spacer(1, 12))
            
            story.append(Spacer(1, 18))
        
        # Footer
        story.append(PageBreak())
        story.append(Paragraph("Gerado por MailCerto", styles['Normal']))
        story.append(Paragraph(datetime.now().strftime("%d/%m/%Y %H:%M:%S"), styles['Normal']))
        
        doc.build(story)
        return output_path
