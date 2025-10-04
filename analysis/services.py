"""
Сервисы для анализа изменений в документах
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from diff_match_patch import diff_match_patch
from django.utils import timezone
from documents.models import Document, DocumentSection, DocumentTable
from .models import Comparison, Change, AnalysisSettings
import json
import re

logger = logging.getLogger(__name__)


class DocumentComparisonService:
    """
    Сервис для сравнения и анализа изменений в документах
    """
    
    def __init__(self):
        self.dmp = diff_match_patch()
        # Настройки для алгоритма diff
        self.dmp.Diff_Timeout = 1.0  # Максимальное время выполнения
        self.dmp.Diff_EditCost = 4   # Стоимость редактирования
    
    def compare_documents(self, comparison: Comparison) -> Dict[str, Any]:
        """
        Основной метод сравнения двух документов
        """
        try:
            start_time = timezone.now()
            
            # Получаем документы
            base_doc = comparison.base_document
            compared_doc = comparison.compared_document
            
            logger.info(f"Начинаем сравнение документов: {base_doc.title} vs {compared_doc.title}")
            
            # Проверяем, что документы обработаны
            if base_doc.status != 'processed' or compared_doc.status != 'processed':
                raise ValueError("Оба документа должны быть обработаны перед сравнением")
            
            # Выполняем анализ
            analysis_result = {
                'text_changes': self._compare_text_content(base_doc, compared_doc),
                'section_changes': self._compare_sections(base_doc, compared_doc),
                'table_changes': self._compare_tables(base_doc, compared_doc),
                'structural_changes': self._analyze_structural_changes(base_doc, compared_doc),
                'metadata_changes': self._compare_metadata(base_doc, compared_doc)
            }
            
            # Подсчитываем общую статистику
            summary = self._calculate_summary(analysis_result)
            analysis_result['summary'] = summary
            
            # Вычисляем время обработки
            processing_time = (timezone.now() - start_time).total_seconds()
            analysis_result['processing_time'] = processing_time
            
            logger.info(f"Сравнение завершено за {processing_time:.2f} секунд")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Ошибка при сравнении документов: {str(e)}")
            raise
    
    def _compare_text_content(self, base_doc: Document, compared_doc: Document) -> List[Dict[str, Any]]:
        """
        Сравнение текстового содержимого документов
        """
        changes = []
        
        # Получаем текстовое содержимое
        base_text = base_doc.content_text or ""
        compared_text = compared_doc.content_text or ""
        
        # Выполняем diff
        diffs = self.dmp.diff_main(base_text, compared_text)
        self.dmp.diff_cleanupSemantic(diffs)
        
        # Обрабатываем изменения
        current_section = "Общий текст"
        change_buffer = []
        
        for diff_type, diff_text in diffs:
            if diff_type == 0:  # Без изменений
                if change_buffer:
                    # Сохраняем накопленные изменения
                    old_text = ''.join([text for change_type, text in change_buffer if change_type == 'removed'])
                    new_text = ''.join([text for change_type, text in change_buffer if change_type == 'added'])
                    changes.append({
                        'type': self._determine_change_type(change_buffer),
                        'section': current_section,
                        'old_content': old_text,
                        'new_content': new_text,
                        'content': new_text,  # Для обратной совместимости
                        'confidence': 1.0,
                        'location': 'text'
                    })
                    change_buffer = []
            elif diff_type == -1:  # Удалено
                change_buffer.append(('removed', diff_text))
            elif diff_type == 1:  # Добавлено
                change_buffer.append(('added', diff_text))
        
        # Обрабатываем оставшиеся изменения
        if change_buffer:
            old_text = ''.join([text for change_type, text in change_buffer if change_type == 'removed'])
            new_text = ''.join([text for change_type, text in change_buffer if change_type == 'added'])
            changes.append({
                'type': self._determine_change_type(change_buffer),
                'section': current_section,
                'old_content': old_text,
                'new_content': new_text,
                'content': new_text,  # Для обратной совместимости
                'confidence': 1.0,
                'location': 'text'
            })
        
        return changes
    
    def _compare_sections(self, base_doc: Document, compared_doc: Document) -> List[Dict[str, Any]]:
        """
        Сравнение разделов документов
        """
        changes = []
        
        # Получаем разделы
        base_sections = {section.title: section for section in base_doc.sections.all()}
        compared_sections = {section.title: section for section in compared_doc.sections.all()}
        
        # Находим добавленные разделы
        for title, section in compared_sections.items():
            if title not in base_sections:
                changes.append({
                    'type': 'added',
                    'section': title,
                    'content': f"Добавлен новый раздел: {title}",
                    'confidence': 1.0,
                    'location': 'section'
                })
        
        # Находим удаленные разделы
        for title, section in base_sections.items():
            if title not in compared_sections:
                changes.append({
                    'type': 'removed',
                    'section': title,
                    'content': f"Удален раздел: {title}",
                    'confidence': 1.0,
                    'location': 'section'
                })
        
        # Сравниваем содержимое общих разделов
        for title in base_sections.keys() & compared_sections.keys():
            base_section = base_sections[title]
            compared_section = compared_sections[title]
            
            if base_section.content != compared_section.content:
                # Выполняем diff для содержимого раздела
                diffs = self.dmp.diff_main(base_section.content, compared_section.content)
                self.dmp.diff_cleanupSemantic(diffs)
                
                section_changes = []
                for diff_type, diff_text in diffs:
                    if diff_type == -1:  # Удалено
                        section_changes.append(('removed', diff_text))
                    elif diff_type == 1:  # Добавлено
                        section_changes.append(('added', diff_text))
                
                if section_changes:
                    changes.append({
                        'type': self._determine_change_type(section_changes),
                        'section': title,
                        'content': ''.join([text for _, text in section_changes]),
                        'confidence': 1.0,
                        'location': 'section'
                    })
        
        return changes
    
    def _compare_tables(self, base_doc: Document, compared_doc: Document) -> List[Dict[str, Any]]:
        """
        Сравнение таблиц в документах
        """
        changes = []
        
        # Получаем таблицы
        base_tables = {table.title: table for table in base_doc.tables.all()}
        compared_tables = {table.title: table for table in compared_doc.tables.all()}
        
        # Находим добавленные таблицы
        for title, table in compared_tables.items():
            if title not in base_tables:
                changes.append({
                    'type': 'added',
                    'section': title,
                    'content': f"Добавлена новая таблица: {title}",
                    'confidence': 1.0,
                    'location': 'table'
                })
        
        # Находим удаленные таблицы
        for title, table in base_tables.items():
            if title not in compared_tables:
                changes.append({
                    'type': 'removed',
                    'section': title,
                    'content': f"Удалена таблица: {title}",
                    'confidence': 1.0,
                    'location': 'table'
                })
        
        # Сравниваем содержимое общих таблиц
        for title in base_tables.keys() & compared_tables.keys():
            base_table = base_tables[title]
            compared_table = compared_tables[title]
            
            table_data_changes = self._compare_table_data(
                base_table.data, 
                compared_table.data
            )
            
            if table_data_changes:
                changes.extend(table_data_changes)
        
        return changes
    
    def _compare_table_data(self, base_data: Dict, compared_data: Dict) -> List[Dict[str, Any]]:
        """
        Сравнение данных таблиц
        """
        changes = []
        
        base_rows = base_data.get('rows', [])
        compared_rows = compared_data.get('rows', [])
        
        # Сравниваем количество строк
        if len(base_rows) != len(compared_rows):
            changes.append({
                'type': 'modified',
                'section': base_data.get('title', 'Таблица'),
                'content': f"Изменено количество строк: {len(base_rows)} → {len(compared_rows)}",
                'confidence': 1.0,
                'location': 'table'
            })
        
        # Сравниваем содержимое строк
        max_rows = max(len(base_rows), len(compared_rows))
        for i in range(max_rows):
            base_row = base_rows[i] if i < len(base_rows) else []
            compared_row = compared_rows[i] if i < len(compared_rows) else []
            
            if base_row != compared_row:
                changes.append({
                    'type': 'modified',
                    'section': f"{base_data.get('title', 'Таблица')} - строка {i+1}",
                    'content': f"Изменена строка: {base_row} → {compared_row}",
                    'confidence': 1.0,
                    'location': 'table'
                })
        
        return changes
    
    def _analyze_structural_changes(self, base_doc: Document, compared_doc: Document) -> List[Dict[str, Any]]:
        """
        Анализ структурных изменений в документах
        """
        changes = []
        
        # Сравниваем структуру
        base_structure = base_doc.content_structure or {}
        compared_structure = compared_doc.content_structure or {}
        
        # Количество абзацев
        base_paragraphs = base_structure.get('total_paragraphs', 0)
        compared_paragraphs = compared_structure.get('total_paragraphs', 0)
        
        if base_paragraphs != compared_paragraphs:
            changes.append({
                'type': 'modified',
                'section': 'Структура документа',
                'content': f"Изменено количество абзацев: {base_paragraphs} → {compared_paragraphs}",
                'confidence': 1.0,
                'location': 'structure'
            })
        
        # Количество таблиц
        base_tables = base_structure.get('total_tables', 0)
        compared_tables = compared_structure.get('total_tables', 0)
        
        if base_tables != compared_tables:
            changes.append({
                'type': 'modified',
                'section': 'Структура документа',
                'content': f"Изменено количество таблиц: {base_tables} → {compared_tables}",
                'confidence': 1.0,
                'location': 'structure'
            })
        
        # Уровни заголовков
        base_headings = set(base_structure.get('heading_levels', []))
        compared_headings = set(compared_structure.get('heading_levels', []))
        
        if base_headings != compared_headings:
            changes.append({
                'type': 'modified',
                'section': 'Структура документа',
                'content': f"Изменены уровни заголовков: {sorted(base_headings)} → {sorted(compared_headings)}",
                'confidence': 1.0,
                'location': 'structure'
            })
        
        return changes
    
    def _compare_metadata(self, base_doc: Document, compared_doc: Document) -> List[Dict[str, Any]]:
        """
        Сравнение метаданных документов
        """
        changes = []
        
        base_metadata = base_doc.metadata or {}
        compared_metadata = compared_doc.metadata or {}
        
        # Сравниваем автора
        base_author = base_metadata.get('author', '')
        compared_author = compared_metadata.get('author', '')
        
        if base_author != compared_author:
            changes.append({
                'type': 'modified',
                'section': 'Метаданные',
                'content': f"Изменен автор: {base_author} → {compared_author}",
                'confidence': 1.0,
                'location': 'metadata'
            })
        
        # Сравниваем дату модификации
        base_modified = base_metadata.get('modified', '')
        compared_modified = compared_metadata.get('modified', '')
        
        if base_modified != compared_modified:
            changes.append({
                'type': 'modified',
                'section': 'Метаданные',
                'content': f"Изменена дата модификации: {base_modified} → {compared_modified}",
                'confidence': 1.0,
                'location': 'metadata'
            })
        
        return changes
    
    def _determine_change_type(self, changes_buffer: List[Tuple[str, str]]) -> str:
        """
        Определяет тип изменения на основе буфера изменений
        """
        has_additions = any(change_type == 'added' for change_type, _ in changes_buffer)
        has_removals = any(change_type == 'removed' for change_type, _ in changes_buffer)
        
        if has_additions and has_removals:
            return 'modified'
        elif has_additions:
            return 'added'
        elif has_removals:
            return 'removed'
        else:
            return 'modified'
    
    def _calculate_summary(self, analysis_result: Dict[str, Any]) -> Dict[str, int]:
        """
        Подсчитывает общую статистику изменений
        """
        summary = {
            'added': 0,
            'removed': 0,
            'modified': 0,
            'total': 0
        }
        
        # Подсчитываем изменения по типам
        for change_type in ['text_changes', 'section_changes', 'table_changes', 'structural_changes', 'metadata_changes']:
            changes = analysis_result.get(change_type, [])
            for change in changes:
                change_type_name = change.get('type', 'modified')
                summary[change_type_name] += 1
                summary['total'] += 1
        
        return summary
    
    def save_comparison_results(self, comparison: Comparison, analysis_result: Dict[str, Any]) -> None:
        """
        Сохраняет результаты сравнения в базу данных
        """
        try:
            # Обновляем основную модель сравнения
            comparison.status = 'completed'
            comparison.completed_date = timezone.now()
            comparison.processing_time = analysis_result.get('processing_time', 0)
            comparison.changes_summary = analysis_result.get('summary', {})
            comparison.detailed_changes = []
            
            # Сохраняем детальные изменения
            for change_type in ['text_changes', 'section_changes', 'table_changes', 'structural_changes', 'metadata_changes']:
                changes = analysis_result.get(change_type, [])
                comparison.detailed_changes.extend(changes)
            
            comparison.save()
            
            # Создаем записи Change для каждого изменения
            Change.objects.filter(comparison=comparison).delete()
            
            for change_data in comparison.detailed_changes:
                Change.objects.create(
                    comparison=comparison,
                    change_type=change_data.get('type', 'modified'),
                    location=change_data.get('location', 'text'),
                    section=change_data.get('section', ''),
                    old_value=change_data.get('old_content', ''),
                    new_value=change_data.get('new_content', change_data.get('content', '')),
                    confidence=change_data.get('confidence', 1.0),
                    context=change_data
                )
            
            logger.info(f"Результаты сравнения {comparison.id} сохранены в БД")
            
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов сравнения {comparison.id}: {str(e)}")
            raise


class AnalysisSettingsService:
    """
    Сервис для работы с настройками анализа
    """
    
    def get_user_settings(self, user) -> AnalysisSettings:
        """
        Получает настройки анализа для пользователя
        """
        settings, created = AnalysisSettings.objects.get_or_create(user=user)
        return settings
    
    def update_settings(self, user, **kwargs) -> AnalysisSettings:
        """
        Обновляет настройки анализа для пользователя
        """
        settings = self.get_user_settings(user)
        
        # Маппинг старых названий на новые
        field_mapping = {
            'ignore_formatting': 'include_text_changes',
            'filter_text_changes': 'include_text_changes',
            'filter_numeric_changes': 'include_table_changes'
        }
        
        for key, value in kwargs.items():
            # Используем маппинг если нужно
            actual_key = field_mapping.get(key, key)
            if hasattr(settings, actual_key):
                setattr(settings, actual_key, value)
        
        settings.save()
        return settings
