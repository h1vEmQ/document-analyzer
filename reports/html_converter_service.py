"""
Сервис для конвертации отчетов в HTML для просмотра в браузере
"""
import os
import logging
from typing import Optional, Dict, Any
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.html import escape
import re

logger = logging.getLogger(__name__)


class HTMLReportConverterService:
    """
    Сервис для конвертации отчетов в HTML формат
    """
    
    def __init__(self):
        self.base_styles = self._get_base_styles()
    
    def _get_base_styles(self) -> str:
        """Возвращает базовые CSS стили для HTML отчета"""
        return """
        <style>
            .report-container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
            }
            .report-header {
                border-bottom: 2px solid #007bff;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }
            .report-title {
                color: #007bff;
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 10px;
            }
            .report-meta {
                display: flex;
                gap: 30px;
                flex-wrap: wrap;
                margin-bottom: 20px;
            }
            .meta-item {
                display: flex;
                flex-direction: column;
            }
            .meta-label {
                font-weight: bold;
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .meta-value {
                color: #333;
                font-size: 1.1em;
            }
            .report-section {
                margin-bottom: 30px;
                padding: 20px;
                border: 1px solid #e9ecef;
                border-radius: 8px;
                background: #f8f9fa;
            }
            .section-title {
                color: #007bff;
                font-size: 1.8em;
                font-weight: bold;
                margin-bottom: 15px;
                border-bottom: 1px solid #dee2e6;
                padding-bottom: 10px;
            }
            .subsection-title {
                color: #495057;
                font-size: 1.4em;
                font-weight: bold;
                margin-bottom: 12px;
                margin-top: 20px;
            }
            .content-text {
                margin-bottom: 15px;
                text-align: justify;
            }
            .highlight-box {
                background: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 5px;
                padding: 15px;
                margin: 15px 0;
            }
            .info-table {
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
                background: white;
                border-radius: 5px;
                overflow: hidden;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .info-table th,
            .info-table td {
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #dee2e6;
            }
            .info-table th {
                background: #007bff;
                color: white;
                font-weight: bold;
            }
            .info-table tr:hover {
                background: #f8f9fa;
            }
            .list-item {
                margin-bottom: 8px;
                padding-left: 20px;
                position: relative;
            }
            .list-item::before {
                content: "•";
                color: #007bff;
                font-weight: bold;
                position: absolute;
                left: 0;
            }
            .badge {
                display: inline-block;
                padding: 4px 8px;
                font-size: 0.8em;
                font-weight: bold;
                border-radius: 4px;
                margin-right: 5px;
            }
            .badge-success { background: #d4edda; color: #155724; }
            .badge-warning { background: #fff3cd; color: #856404; }
            .badge-danger { background: #f8d7da; color: #721c24; }
            .badge-info { background: #d1ecf1; color: #0c5460; }
            .badge-secondary { background: #e2e3e5; color: #383d41; }
            .document-comparison {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
                margin: 20px 0;
            }
            .document-section {
                padding: 15px;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                background: white;
            }
            .document-title {
                font-weight: bold;
                color: #007bff;
                margin-bottom: 10px;
                font-size: 1.2em;
            }
            @media (max-width: 768px) {
                .document-comparison {
                    grid-template-columns: 1fr;
                }
                .report-meta {
                    flex-direction: column;
                    gap: 15px;
                }
            }
        </style>
        """
    
    def convert_report_to_html(self, report) -> str:
        """
        Конвертирует отчет в HTML для просмотра в браузере
        
        Args:
            report: Объект отчета
            
        Returns:
            str: HTML содержимое отчета
        """
        try:
            # Получаем данные отчета в зависимости от формата
            if report.format.lower() == 'pdf':
                return self._convert_pdf_to_html(report)
            elif report.format.lower() == 'docx':
                return self._convert_docx_to_html(report)
            else:
                return self._create_fallback_html(report)
                
        except Exception as e:
            logger.error(f"Ошибка конвертации отчета {report.id} в HTML: {e}")
            return self._create_error_html(report, str(e))
    
    def _convert_pdf_to_html(self, report) -> str:
        """Конвертирует PDF отчет в HTML (упрощенная версия)"""
        # Для PDF создаем базовую HTML структуру с информацией об отчете
        # В реальном проекте здесь можно использовать библиотеки для извлечения текста из PDF
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{escape(report.title)}</title>
            {self.base_styles}
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">{escape(report.title)}</h1>
                    <div class="report-meta">
                        <div class="meta-item">
                            <span class="meta-label">Формат</span>
                            <span class="meta-value">PDF</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Дата создания</span>
                            <span class="meta-value">{report.generated_date.strftime('%d.%m.%Y %H:%M')}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Статус</span>
                            <span class="meta-value">
                                <span class="badge badge-{'success' if report.status == 'ready' else 'warning'}">
                                    {report.get_status_display()}
                                </span>
                            </span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Размер файла</span>
                            <span class="meta-value">{report.get_file_size_mb()} МБ</span>
                        </div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Информация об отчете</h2>
                    <table class="info-table">
                        <tr>
                            <th>Параметр</th>
                            <th>Значение</th>
                        </tr>
                        <tr>
                            <td>Название</td>
                            <td>{escape(report.title)}</td>
                        </tr>
                        <tr>
                            <td>Формат</td>
                            <td>{report.format.upper()}</td>
                        </tr>
                        <tr>
                            <td>Шаблон</td>
                            <td>{escape(report.template_used or 'Не указан')}</td>
                        </tr>
                        <tr>
                            <td>Версия</td>
                            <td>{report.version}</td>
                        </tr>
                        <tr>
                            <td>Дата генерации</td>
                            <td>{report.generated_date.strftime('%d.%m.%Y %H:%M')}</td>
                        </tr>
                        <tr>
                            <td>Статус</td>
                            <td>
                                <span class="badge badge-{'success' if report.status == 'ready' else 'warning'}">
                                    {report.get_status_display()}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td>Размер файла</td>
                            <td>{report.get_file_size_mb()} МБ</td>
                        </tr>
                    </table>
                </div>
                
                {self._get_comparison_info_html(report)}
                
                <div class="highlight-box">
                    <strong>Примечание:</strong> Это PDF отчет. Для просмотра полного содержимого используйте кнопку "Скачать отчет".
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Действия</h2>
                    <p>Для просмотра полного содержимого PDF отчета:</p>
                    <div class="list-item">Нажмите кнопку "Скачать отчет" для сохранения файла</div>
                    <div class="list-item">Откройте файл в PDF просмотрщике</div>
                    <div class="list-item">Или используйте встроенный просмотрщик браузера</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _convert_docx_to_html(self, report) -> str:
        """Конвертирует DOCX отчет в HTML (упрощенная версия)"""
        # Для DOCX создаем базовую HTML структуру
        # В реальном проекте здесь можно использовать python-docx для извлечения содержимого
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{escape(report.title)}</title>
            {self.base_styles}
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">{escape(report.title)}</h1>
                    <div class="report-meta">
                        <div class="meta-item">
                            <span class="meta-label">Формат</span>
                            <span class="meta-value">DOCX</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Дата создания</span>
                            <span class="meta-value">{report.generated_date.strftime('%d.%m.%Y %H:%M')}</span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Статус</span>
                            <span class="meta-value">
                                <span class="badge badge-{'success' if report.status == 'ready' else 'warning'}">
                                    {report.get_status_display()}
                                </span>
                            </span>
                        </div>
                        <div class="meta-item">
                            <span class="meta-label">Размер файла</span>
                            <span class="meta-value">{report.get_file_size_mb()} МБ</span>
                        </div>
                    </div>
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Информация об отчете</h2>
                    <table class="info-table">
                        <tr>
                            <th>Параметр</th>
                            <th>Значение</th>
                        </tr>
                        <tr>
                            <td>Название</td>
                            <td>{escape(report.title)}</td>
                        </tr>
                        <tr>
                            <td>Формат</td>
                            <td>{report.format.upper()}</td>
                        </tr>
                        <tr>
                            <td>Шаблон</td>
                            <td>{escape(report.template_used or 'Не указан')}</td>
                        </tr>
                        <tr>
                            <td>Версия</td>
                            <td>{report.version}</td>
                        </tr>
                        <tr>
                            <td>Дата генерации</td>
                            <td>{report.generated_date.strftime('%d.%m.%Y %H:%M')}</td>
                        </tr>
                        <tr>
                            <td>Статус</td>
                            <td>
                                <span class="badge badge-{'success' if report.status == 'ready' else 'warning'}">
                                    {report.get_status_display()}
                                </span>
                            </td>
                        </tr>
                        <tr>
                            <td>Размер файла</td>
                            <td>{report.get_file_size_mb()} МБ</td>
                        </tr>
                    </table>
                </div>
                
                {self._get_comparison_info_html(report)}
                
                <div class="highlight-box">
                    <strong>Примечание:</strong> Это DOCX отчет. Для просмотра полного содержимого используйте кнопку "Скачать отчет".
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Действия</h2>
                    <p>Для просмотра полного содержимого DOCX отчета:</p>
                    <div class="list-item">Нажмите кнопку "Скачать отчет" для сохранения файла</div>
                    <div class="list-item">Откройте файл в Microsoft Word или LibreOffice Writer</div>
                    <div class="list-item">Или используйте онлайн версию Office 365</div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _get_comparison_info_html(self, report) -> str:
        """Возвращает HTML с информацией о сравнении"""
        if not report.comparison:
            return ""
        
        comparison = report.comparison
        
        html = f"""
        <div class="report-section">
            <h2 class="section-title">Информация о сравнении</h2>
            <table class="info-table">
                <tr>
                    <th>Параметр</th>
                    <th>Значение</th>
                </tr>
                <tr>
                    <td>Название сравнения</td>
                    <td>{escape(comparison.title)}</td>
                </tr>
                <tr>
                    <td>Тип анализа</td>
                    <td>{escape(comparison.get_analysis_type_display())}</td>
                </tr>
                <tr>
                    <td>Метод анализа</td>
                    <td>{escape(comparison.analysis_method or 'Не указан')}</td>
                </tr>
                <tr>
                    <td>Статус анализа</td>
                    <td>
                        <span class="badge badge-{'success' if comparison.status == 'completed' else 'warning'}">
                            {comparison.get_status_display()}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td>Дата создания</td>
                    <td>{comparison.created_date.strftime('%d.%m.%Y %H:%M')}</td>
                </tr>
            </table>
        </div>
        
        <div class="report-section">
            <h2 class="section-title">Сравниваемые документы</h2>
            <div class="document-comparison">
                <div class="document-section">
                    <div class="document-title">Базовый документ</div>
                    <div class="content-text">
                        <strong>Название:</strong> {escape(comparison.base_document.title)}<br>
                        <strong>Версия:</strong> {comparison.base_document.version}<br>
                        <strong>Дата загрузки:</strong> {comparison.base_document.upload_date.strftime('%d.%m.%Y %H:%M')}<br>
                        <strong>Статус:</strong> {comparison.base_document.get_status_display()}
                    </div>
                </div>
                <div class="document-section">
                    <div class="document-title">Сравниваемый документ</div>
                    <div class="content-text">
                        <strong>Название:</strong> {escape(comparison.compared_document.title)}<br>
                        <strong>Версия:</strong> {comparison.compared_document.version}<br>
                        <strong>Дата загрузки:</strong> {comparison.compared_document.upload_date.strftime('%d.%m.%Y %H:%M')}<br>
                        <strong>Статус:</strong> {comparison.compared_document.get_status_display()}
                    </div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _create_fallback_html(self, report) -> str:
        """Создает базовый HTML для неизвестного формата"""
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{escape(report.title)}</title>
            {self.base_styles}
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">{escape(report.title)}</h1>
                </div>
                
                <div class="highlight-box">
                    <strong>Внимание:</strong> Неподдерживаемый формат отчета: {report.format}
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Информация об отчете</h2>
                    <p>Название: {escape(report.title)}</p>
                    <p>Формат: {report.format}</p>
                    <p>Дата создания: {report.generated_date.strftime('%d.%m.%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_error_html(self, report, error_message: str) -> str:
        """Создает HTML с сообщением об ошибке"""
        return f"""
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Ошибка - {escape(report.title)}</title>
            {self.base_styles}
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">Ошибка просмотра отчета</h1>
                </div>
                
                <div class="highlight-box" style="background: #f8d7da; border-color: #f5c6cb; color: #721c24;">
                    <strong>Ошибка:</strong> {escape(error_message)}
                </div>
                
                <div class="report-section">
                    <h2 class="section-title">Информация об отчете</h2>
                    <p>Название: {escape(report.title)}</p>
                    <p>Формат: {report.format}</p>
                    <p>Дата создания: {report.generated_date.strftime('%d.%m.%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
