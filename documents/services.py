"""
Сервисы для работы с документами Word
"""
import os
import logging
from typing import Dict, List, Any, Optional
from docx import Document as DocxDocument
from docx.document import Document as DocumentType
from docx.table import Table
from docx.text.paragraph import Paragraph
from django.core.files.uploadedfile import UploadedFile
from django.core.exceptions import ValidationError
from .models import Document, DocumentSection, DocumentTable, DocumentTableAnalysis

logger = logging.getLogger(__name__)


class DocumentParserService:
    """
    Сервис для парсинга документов Word (.docx)
    """
    
    def __init__(self):
        self.supported_formats = ['.docx']
        self.max_file_size = 10 * 1024 * 1024  # 10 МБ
    
    def validate_file(self, file: UploadedFile) -> bool:
        """
        Валидация загруженного файла
        """
        # Проверка размера
        if file.size > self.max_file_size:
            raise ValidationError(f"Размер файла превышает {self.max_file_size // (1024*1024)} МБ")
        
        # Проверка расширения
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in self.supported_formats:
            raise ValidationError(f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(self.supported_formats)}")
        
        return True
    
    def parse_document(self, document: Document) -> Dict[str, Any]:
        """
        Парсинг документа и извлечение содержимого
        """
        try:
            # Открываем документ
            docx_doc = DocxDocument(document.file.path)
            
            # Извлекаем содержимое
            content_data = {
                'text_content': self._extract_text(docx_doc),
                'sections': self._extract_sections(docx_doc),
                'tables': self._extract_tables(docx_doc),
                'metadata': self._extract_metadata(docx_doc, document),
                'structure': self._analyze_structure(docx_doc)
            }
            
            # Сохраняем извлеченный текст в модель
            document.content_text = content_data['text_content']
            document.save(update_fields=['content_text'])
            
            # Автоматически анализируем таблицы, если они есть
            if content_data.get('tables'):
                try:
                    table_analysis_service = DocumentTableAnalysisService()
                    analysis_result = table_analysis_service.analyze_document_tables(document)
                    if analysis_result['success']:
                        logger.info(f"Автоматический анализ таблиц выполнен для документа {document.title}: {analysis_result.get('tables_count', 0)} таблиц")
                    else:
                        logger.warning(f"Ошибка автоматического анализа таблиц для документа {document.title}: {analysis_result.get('error', 'Неизвестная ошибка')}")
                except Exception as e:
                    logger.error(f"Ошибка при автоматическом анализе таблиц документа {document.title}: {str(e)}")
            
            logger.info(f"Документ {document.title} успешно обработан")
            return {
                "success": True,
                "content_data": content_data
            }
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге документа {document.title}: {str(e)}")
            return {
                "success": False,
                "error": f"Ошибка при обработке документа: {str(e)}"
            }
    
    def save_parsed_content(self, document: Document, content_data: Dict[str, Any]) -> None:
        """
        Сохраняет распарсенное содержимое документа в базу данных
        """
        try:
            # Удаляем старые данные
            DocumentSection.objects.filter(document=document).delete()
            DocumentTable.objects.filter(document=document).delete()
            
            # Сохраняем разделы
            for section_data in content_data.get('sections', []):
                DocumentSection.objects.create(
                    document=document,
                    title=section_data['title'],
                    content=section_data['content'],
                    level=section_data['level'],
                    order=section_data['order']
                )
            
            # Сохраняем таблицы
            for table_data in content_data.get('tables', []):
                DocumentTable.objects.create(
                    document=document,
                    title=table_data['title'],
                    content=table_data['content'],
                    rows=table_data['rows'],
                    columns=table_data['columns'],
                    order=table_data['order']
                )
            
            logger.info(f"Содержимое документа {document.title} сохранено в БД")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении содержимого документа {document.title}: {str(e)}")
            raise
    
    def _extract_text(self, doc: DocumentType) -> str:
        """
        Извлечение всего текстового содержимого включая таблицы
        """
        full_text = []
        
        # Извлекаем текст из параграфов
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        
        # Извлекаем текст из таблиц
        for table in doc.tables:
            table_text = []
            for row in table.rows:
                row_text = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text.append(cell_text)
                if row_text:
                    table_text.append(' | '.join(row_text))
            
            if table_text:
                full_text.append('\n'.join(table_text))
        
        return '\n\n'.join(full_text)
    
    def _extract_sections(self, doc: DocumentType) -> List[Dict[str, Any]]:
        """
        Извлечение разделов документа
        """
        sections = []
        current_section = None
        order = 0
        
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            
            # Определяем уровень заголовка по стилю
            level = self._get_heading_level(paragraph)
            
            if level > 0:  # Это заголовок
                # Сохраняем предыдущий раздел
                if current_section:
                    sections.append(current_section)
                
                # Создаем новый раздел
                current_section = {
                    'title': text,
                    'level': level,
                    'order': order,
                    'content': '',
                    'paragraphs': []
                }
                order += 1
            else:
                # Добавляем абзац к текущему разделу
                if current_section:
                    current_section['content'] += text + '\n\n'
                    current_section['paragraphs'].append(text)
                else:
                    # Если нет текущего раздела, создаем общий
                    if not current_section:
                        current_section = {
                            'title': 'Общий текст',
                            'level': 0,
                            'order': order,
                            'content': text + '\n\n',
                            'paragraphs': [text]
                        }
                    else:
                        current_section['content'] += text + '\n\n'
                        current_section['paragraphs'].append(text)
        
        # Добавляем последний раздел
        if current_section:
            sections.append(current_section)
        
        return sections
    
    def _extract_tables(self, doc: DocumentType) -> List[Dict[str, Any]]:
        """
        Извлечение таблиц из документа
        """
        tables = []
        
        for i, table in enumerate(doc.tables):
            table_data = {
                'order': i,
                'title': f'Таблица {i + 1}',
                'rows': [],
                'headers': [],
                'row_count': len(table.rows),
                'col_count': len(table.columns) if table.rows else 0
            }
            
            # Извлекаем данные таблицы
            for row_idx, row in enumerate(table.rows):
                row_data = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    row_data.append(cell_text)
                
                table_data['rows'].append(row_data)
                
                # Первая строка считается заголовками
                if row_idx == 0:
                    table_data['headers'] = row_data
            
            tables.append(table_data)
        
        return tables
    
    def _extract_metadata(self, doc: DocumentType, document: Document) -> Dict[str, Any]:
        """
        Извлечение метаданных документа
        """
        core_props = doc.core_properties
        
        metadata = {
            'title': core_props.title or document.title,
            'author': core_props.author or '',
            'created': core_props.created.isoformat() if core_props.created else None,
            'modified': core_props.modified.isoformat() if core_props.modified else None,
            'subject': core_props.subject or '',
            'keywords': core_props.keywords or '',
            'comments': core_props.comments or '',
            'word_count': len(doc.paragraphs),
            'table_count': len(doc.tables),
            'page_count': self._estimate_page_count(doc)
        }
        
        return metadata
    
    def _analyze_structure(self, doc: DocumentType) -> Dict[str, Any]:
        """
        Анализ структуры документа
        """
        structure = {
            'total_paragraphs': len(doc.paragraphs),
            'total_tables': len(doc.tables),
            'heading_levels': set(),
            'has_tables': len(doc.tables) > 0,
            'has_images': False,  # Пока не реализовано
            'estimated_pages': self._estimate_page_count(doc)
        }
        
        # Анализируем уровни заголовков
        for paragraph in doc.paragraphs:
            level = self._get_heading_level(paragraph)
            if level > 0:
                structure['heading_levels'].add(level)
        
        structure['heading_levels'] = sorted(list(structure['heading_levels']))
        
        return structure
    
    def _get_heading_level(self, paragraph: Paragraph) -> int:
        """
        Определение уровня заголовка
        """
        style_name = paragraph.style.name.lower()
        
        if 'heading 1' in style_name or 'заголовок 1' in style_name:
            return 1
        elif 'heading 2' in style_name or 'заголовок 2' in style_name:
            return 2
        elif 'heading 3' in style_name or 'заголовок 3' in style_name:
            return 3
        elif 'heading 4' in style_name or 'заголовок 4' in style_name:
            return 4
        elif 'heading 5' in style_name or 'заголовок 5' in style_name:
            return 5
        elif 'heading 6' in style_name or 'заголовок 6' in style_name:
            return 6
        else:
            return 0
    
    def _estimate_page_count(self, doc: DocumentType) -> int:
        """
        Примерная оценка количества страниц
        """
        # Простая оценка: примерно 500 символов на страницу
        total_chars = sum(len(p.text) for p in doc.paragraphs)
        estimated_pages = max(1, total_chars // 500)
        return estimated_pages
    
    def save_parsed_content(self, document: Document, content_data: Dict[str, Any]) -> None:
        """
        Сохранение извлеченного содержимого в базу данных
        """
        try:
            # Обновляем основной документ
            document.content_text = content_data['text_content']
            document.content_structure = content_data['structure']
            document.metadata = content_data['metadata']
            document.status = 'processed'
            document.save()
            
            # Сохраняем разделы
            DocumentSection.objects.filter(document=document).delete()
            for section_data in content_data['sections']:
                DocumentSection.objects.create(
                    document=document,
                    title=section_data['title'],
                    content=section_data['content'],
                    order=section_data['order'],
                    level=section_data['level']
                )
            
            # Сохраняем таблицы
            DocumentTable.objects.filter(document=document).delete()
            for table_data in content_data['tables']:
                DocumentTable.objects.create(
                    document=document,
                    title=table_data['title'],
                    data=table_data,
                    order=table_data['order']
                )
            
            logger.info(f"Содержимое документа {document.title} сохранено в БД")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении содержимого документа {document.title}: {str(e)}")
            raise


class DocumentValidationService:
    """
    Сервис для валидации документов
    """
    
    def __init__(self):
        self.allowed_extensions = ['.docx']
        self.max_file_size = 10 * 1024 * 1024  # 10 МБ
    
    def validate_upload(self, file: UploadedFile) -> Dict[str, Any]:
        """
        Полная валидация загруженного файла
        """
        validation_result = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'file_info': {}
        }
        
        # Проверка размера
        if file.size > self.max_file_size:
            validation_result['is_valid'] = False
            validation_result['errors'].append(
                f"Размер файла ({file.size // (1024*1024)} МБ) превышает максимально допустимый ({self.max_file_size // (1024*1024)} МБ)"
            )
        
        # Проверка расширения
        file_extension = os.path.splitext(file.name)[1].lower()
        if file_extension not in self.allowed_extensions:
            validation_result['is_valid'] = False
            validation_result['errors'].append(
                f"Неподдерживаемый формат файла. Поддерживаются: {', '.join(self.allowed_extensions)}"
            )
        
        # Проверка имени файла
        if len(file.name) > 255:
            validation_result['is_valid'] = False
            validation_result['errors'].append("Имя файла слишком длинное (максимум 255 символов)")
        
        # Информация о файле
        validation_result['file_info'] = {
            'name': file.name,
            'size': file.size,
            'size_mb': round(file.size / (1024 * 1024), 2),
            'extension': file_extension,
            'content_type': getattr(file, 'content_type', 'application/octet-stream')
        }
        
        return validation_result


class DocumentKeyPointsService:
    """
    Сервис для генерации ключевых моментов документа
    """
    
    def __init__(self):
        from analysis.ollama_service import OllamaService
        from django.utils import timezone
        from settings.models import ApplicationSettings
        
        # Получаем модель из настроек приложения
        settings = ApplicationSettings.get_settings()
        model = settings.default_neural_network_model or 'llama3'
        
        self.ollama_service = OllamaService(model=model)
        self.timezone = timezone
    
    def generate_key_points(self, document):
        """
        Генерирует ключевые моменты для документа
        
        Args:
            document: Объект Document
            
        Returns:
            Dict с результатами генерации
        """
        try:
            if not document.has_content():
                raise ValueError("Документ должен быть обработан перед генерацией ключевых моментов")
            
            # Получаем содержимое документа
            content = document.get_content_text()
            
            if not content or len(content.strip()) < 50:
                raise ValueError("Недостаточно содержимого для генерации ключевых моментов")
            
            logger.info(f"Начинаем генерацию ключевых моментов для документа {document.id} с содержимым {len(content)} символов")
            
            # Генерируем ключевые моменты через Ollama
            result = self.ollama_service.extract_key_points(content)
            
            logger.info(f"Результат от Ollama для документа {document.id}: {result.get('success', False)}")
            
            if result.get("success", False):
                key_points_result = result.get("key_points_result", {})
                
                # Извлекаем ключевые моменты
                key_points = key_points_result.get("key_points", [])
                summary = key_points_result.get("summary", "")
                main_topics = key_points_result.get("main_topics", [])
                
                logger.info(f"Получено ключевых моментов: {len(key_points)}")
                
                # Сохраняем ключевые моменты в документ
                document.key_points = key_points
                document.key_points_generated_date = self.timezone.now()
                document.save(update_fields=['key_points', 'key_points_generated_date'])
                
                logger.info(f"Ключевые моменты сохранены для документа {document.id}")
                
                return {
                    "success": True,
                    "key_points": key_points,
                    "summary": summary,
                    "main_topics": main_topics
                }
            else:
                error_msg = result.get("error", "Неизвестная ошибка при генерации")
                logger.error(f"Ollama вернул ошибку для документа {document.id}: {error_msg}")
                raise Exception(error_msg)
                
        except Exception as e:
            logger.error(f"Ошибка при генерации ключевых моментов для документа {document.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }


class DocumentTableAnalysisService:
    """
    Сервис для анализа таблиц в документах
    """
    
    def __init__(self):
        import re
        from django.utils import timezone
        
        self.re = re
        self.timezone = timezone
        self.logger = logging.getLogger(__name__)
    
    def analyze_document_tables(self, document: Document) -> Dict[str, Any]:
        """
        Анализирует все таблицы в документе
        
        Args:
            document: Объект Document
            
        Returns:
            Dict с результатами анализа
        """
        try:
            if not document.has_content():
                raise ValueError("Документ должен быть обработан перед анализом таблиц")
            
            # Получаем все таблицы документа
            tables = DocumentTable.objects.filter(document=document).order_by('order')
            
            if not tables.exists():
                return {
                    "success": True,
                    "message": "В документе нет таблиц для анализа",
                    "tables_count": 0,
                    "analyses": []
                }
            
            analyses = []
            total_metrics = {
                'total_rows': 0,
                'total_columns': 0,
                'total_cells': 0,
                'total_empty_cells': 0,
                'total_numeric_cells': 0,
                'total_text_cells': 0
            }
            
            for table in tables:
                analysis = self._analyze_single_table(table)
                analyses.append(analysis)
                
                # Суммируем метрики
                total_metrics['total_rows'] += analysis['row_count']
                total_metrics['total_columns'] += analysis['column_count']
                total_metrics['total_cells'] += analysis['cell_count']
                total_metrics['total_empty_cells'] += analysis['empty_cells_count']
                total_metrics['total_numeric_cells'] += analysis['numeric_cells_count']
                total_metrics['total_text_cells'] += analysis['text_cells_count']
            
            # Сохраняем анализы в базу данных
            self._save_table_analyses(document, analyses)
            
            self.logger.info(f"Анализ таблиц завершен для документа {document.id}: {len(analyses)} таблиц")
            
            return {
                "success": True,
                "tables_count": len(analyses),
                "analyses": analyses,
                "summary": self._generate_summary(total_metrics, len(analyses))
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе таблиц документа {document.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _analyze_single_table(self, table: DocumentTable) -> Dict[str, Any]:
        """
        Анализирует одну таблицу
        
        Args:
            table: Объект DocumentTable
            
        Returns:
            Dict с результатами анализа таблицы
        """
        try:
            # Парсим данные таблицы
            table_data = table.data
            
            if not table_data or 'rows' not in table_data:
                return {
                    "success": False,
                    "error": "Некорректные данные таблицы"
                }
            
            rows = table_data['rows']
            row_count = len(rows)
            column_count = len(rows[0]) if rows else 0
            cell_count = row_count * column_count
            
            # Анализируем содержимое ячеек
            empty_cells = 0
            numeric_cells = 0
            text_cells = 0
            has_headers = False
            header_row_count = 0
            
            # Анализируем первую строку на предмет заголовков
            if rows:
                first_row = rows[0]
                header_indicators = 0
                
                for cell in first_row:
                    cell_text = str(cell).strip().lower()
                    # Проверяем, является ли ячейка заголовком
                    if (self._is_header_cell(cell_text) or 
                        cell_text in ['№', 'номер', 'название', 'наименование', 'количество', 'сумма', 'дата']):
                        header_indicators += 1
                
                # Если больше половины ячеек первой строки похожи на заголовки
                if header_indicators > column_count / 2:
                    has_headers = True
                    header_row_count = 1
            
            # Анализируем все ячейки
            for row in rows:
                for cell in row:
                    cell_text = str(cell).strip()
                    
                    if not cell_text:
                        empty_cells += 1
                    elif self._is_numeric(cell_text):
                        numeric_cells += 1
                    else:
                        text_cells += 1
            
            # Определяем тип таблицы
            table_type = self._determine_table_type(rows, numeric_cells, text_cells)
            
            # Определяем основную тему
            main_topic = self._extract_main_topic(rows)
            
            # Извлекаем ключевые метрики
            key_metrics = self._extract_key_metrics(rows, numeric_cells)
            
            return {
                "success": True,
                "table_id": table.id,
                "table_title": table.title,
                "row_count": row_count,
                "column_count": column_count,
                "cell_count": cell_count,
                "empty_cells_count": empty_cells,
                "numeric_cells_count": numeric_cells,
                "text_cells_count": text_cells,
                "has_headers": has_headers,
                "header_row_count": header_row_count,
                "table_type": table_type,
                "main_topic": main_topic,
                "key_metrics": key_metrics,
                "fill_percentage": round(((cell_count - empty_cells) / cell_count) * 100, 2) if cell_count > 0 else 0,
                "numeric_percentage": round((numeric_cells / cell_count) * 100, 2) if cell_count > 0 else 0,
                "text_percentage": round((text_cells / cell_count) * 100, 2) if cell_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе таблицы {table.id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _is_numeric(self, text: str) -> bool:
        """Проверяет, является ли текст числовым"""
        try:
            # Убираем пробелы и заменяем запятые на точки
            cleaned_text = text.replace(',', '.').replace(' ', '')
            
            # Проверяем на число
            float(cleaned_text)
            return True
        except (ValueError, TypeError):
            # Проверяем на процент
            if cleaned_text.endswith('%'):
                try:
                    float(cleaned_text[:-1])
                    return True
                except ValueError:
                    pass
            
            # Проверяем на валюту (рубли, доллары и т.д.)
            currency_patterns = [
                r'^\d+[\s,]*\d*[\s,]*\d*\s*(руб|р\.|₽|дол|usd|\$|€|eur)',
                r'^\d+[\s,]*\d*[\s,]*\d*\s*(тыс|млн|млрд)',
                r'^\d+[\s,]*\d*[\s,]*\d*\s*(тыс\.|млн\.|млрд\.)'
            ]
            
            for pattern in currency_patterns:
                if self.re.match(pattern, cleaned_text.lower()):
                    return True
            
            return False
    
    def _is_header_cell(self, text: str) -> bool:
        """Проверяет, является ли ячейка заголовком"""
        header_keywords = [
            'название', 'наименование', 'имя', 'заголовок',
            'номер', '№', 'код', 'id',
            'дата', 'время', 'период',
            'количество', 'сумма', 'стоимость', 'цена',
            'статус', 'состояние', 'результат',
            'описание', 'комментарий', 'примечание'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in header_keywords)
    
    def _determine_table_type(self, rows: List[List], numeric_cells: int, text_cells: int) -> str:
        """Определяет тип таблицы"""
        if not rows:
            return "пустая"
        
        total_cells = len(rows) * len(rows[0]) if rows else 0
        
        if total_cells == 0:
            return "пустая"
        
        numeric_ratio = numeric_cells / total_cells
        
        if numeric_ratio > 0.7:
            return "числовая"
        elif numeric_ratio > 0.3:
            return "смешанная"
        else:
            return "текстовая"
    
    def _extract_main_topic(self, rows: List[List]) -> str:
        """Извлекает основную тему таблицы"""
        if not rows or not rows[0]:
            return "неизвестно"
        
        # Берем первую строку как потенциальные заголовки
        first_row = rows[0]
        topics = []
        
        for cell in first_row:
            cell_text = str(cell).strip()
            if cell_text and len(cell_text) > 3:
                topics.append(cell_text)
        
        if topics:
            # Возвращаем самый длинный заголовок как основную тему
            return max(topics, key=len)
        
        return "неизвестно"
    
    def _extract_key_metrics(self, rows: List[List], numeric_cells: int) -> List[Dict[str, Any]]:
        """Извлекает ключевые метрики из таблицы"""
        metrics = []
        
        if not rows:
            return metrics
        
        # Базовая статистика
        metrics.append({
            "name": "Общее количество строк",
            "value": len(rows),
            "type": "count"
        })
        
        metrics.append({
            "name": "Количество столбцов",
            "value": len(rows[0]) if rows else 0,
            "type": "count"
        })
        
        metrics.append({
            "name": "Числовых ячеек",
            "value": numeric_cells,
            "type": "count"
        })
        
        # Если есть числовые данные, пытаемся найти суммы и средние
        if numeric_cells > 0:
            numeric_values = []
            for row in rows:
                for cell in row:
                    cell_text = str(cell).strip()
                    if self._is_numeric(cell_text):
                        try:
                            cleaned = cell_text.replace(',', '.').replace(' ', '')
                            # Убираем валютные символы
                            cleaned = self.re.sub(r'[^\d.,]', '', cleaned)
                            if cleaned:
                                numeric_values.append(float(cleaned))
                        except ValueError:
                            continue
            
            if numeric_values:
                metrics.append({
                    "name": "Сумма всех значений",
                    "value": sum(numeric_values),
                    "type": "sum"
                })
                
                metrics.append({
                    "name": "Среднее значение",
                    "value": sum(numeric_values) / len(numeric_values),
                    "type": "average"
                })
                
                metrics.append({
                    "name": "Максимальное значение",
                    "value": max(numeric_values),
                    "type": "max"
                })
                
                metrics.append({
                    "name": "Минимальное значение",
                    "value": min(numeric_values),
                    "type": "min"
                })
        
        return metrics
    
    def _generate_summary(self, total_metrics: Dict[str, int], tables_count: int) -> Dict[str, Any]:
        """Генерирует общую сводку по всем таблицам"""
        if tables_count == 0:
            return {
                "message": "В документе нет таблиц",
                "tables_count": 0
            }
        
        avg_rows = total_metrics['total_rows'] / tables_count if tables_count > 0 else 0
        avg_columns = total_metrics['total_columns'] / tables_count if tables_count > 0 else 0
        
        fill_percentage = 0
        if total_metrics['total_cells'] > 0:
            filled_cells = total_metrics['total_cells'] - total_metrics['total_empty_cells']
            fill_percentage = round((filled_cells / total_metrics['total_cells']) * 100, 2)
        
        return {
            "tables_count": tables_count,
            "total_rows": total_metrics['total_rows'],
            "total_columns": total_metrics['total_columns'],
            "total_cells": total_metrics['total_cells'],
            "avg_rows_per_table": round(avg_rows, 1),
            "avg_columns_per_table": round(avg_columns, 1),
            "fill_percentage": fill_percentage,
            "numeric_percentage": round((total_metrics['total_numeric_cells'] / total_metrics['total_cells']) * 100, 2) if total_metrics['total_cells'] > 0 else 0,
            "text_percentage": round((total_metrics['total_text_cells'] / total_metrics['total_cells']) * 100, 2) if total_metrics['total_cells'] > 0 else 0
        }
    
    def _save_table_analyses(self, document: Document, analyses: List[Dict[str, Any]]) -> None:
        """Сохраняет анализы таблиц в базу данных"""
        try:
            # Удаляем старые анализы
            DocumentTableAnalysis.objects.filter(document=document).delete()
            
            # Сохраняем новые анализы
            for analysis in analyses:
                if analysis.get('success', False):
                    table = DocumentTable.objects.get(id=analysis['table_id']) if analysis.get('table_id') else None
                    
                    DocumentTableAnalysis.objects.create(
                        document=document,
                        table=table,
                        row_count=analysis['row_count'],
                        column_count=analysis['column_count'],
                        cell_count=analysis['cell_count'],
                        empty_cells_count=analysis['empty_cells_count'],
                        numeric_cells_count=analysis['numeric_cells_count'],
                        text_cells_count=analysis['text_cells_count'],
                        has_headers=analysis['has_headers'],
                        header_row_count=analysis['header_row_count'],
                        table_type=analysis['table_type'],
                        main_topic=analysis['main_topic'],
                        key_metrics=analysis['key_metrics']
                    )
            
            self.logger.info(f"Анализы таблиц сохранены для документа {document.id}")
            
        except Exception as e:
            self.logger.error(f"Ошибка при сохранении анализов таблиц для документа {document.id}: {str(e)}")
            raise
