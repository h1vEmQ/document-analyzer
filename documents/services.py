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
from .models import Document, DocumentSection, DocumentTable

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
    
    def _extract_text(self, doc: DocumentType) -> str:
        """
        Извлечение всего текстового содержимого
        """
        full_text = []
        
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                full_text.append(paragraph.text.strip())
        
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
