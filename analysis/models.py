from django.db import models
from django.contrib.auth import get_user_model
from documents.models import Document

User = get_user_model()


class Comparison(models.Model):
    """
    Модель для хранения результатов сравнения документов
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает'),
        ('processing', 'Обрабатывается'),
        ('completed', 'Завершено'),
        ('error', 'Ошибка'),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name='Название сравнения'
    )
    
    base_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='base_comparisons',
        verbose_name='Базовый документ'
    )
    
    compared_document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='compared_comparisons',
        verbose_name='Сравниваемый документ'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    completed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата завершения'
    )
    
    processing_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Время обработки (сек)'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comparisons',
        verbose_name='Пользователь'
    )
    
    # Результаты анализа
    changes_summary = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Сводка изменений'
    )
    
    detailed_changes = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Детальные изменения'
    )
    
    # Новые поля для Ollama анализа
    analysis_type = models.CharField(
        max_length=20,
        choices=[
            ('diff', 'Сравнение различий'),
            ('ollama', 'Анализ нейросетью'),
        ],
        default='diff',
        verbose_name='Тип анализа'
    )
    
    analysis_method = models.CharField(
        max_length=50,
        blank=True,
        verbose_name='Метод анализа'
    )
    
    analysis_result = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Результат анализа'
    )
    
    class Meta:
        verbose_name = 'Сравнение документов'
        verbose_name_plural = 'Сравнения документов'
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.title} ({self.base_document.title} vs {self.compared_document.title})"
    
    def get_total_changes(self):
        """Возвращает общее количество изменений"""
        summary = self.changes_summary or {}
        return (
            summary.get('added', 0) +
            summary.get('removed', 0) +
            summary.get('modified', 0)
        )
    
    def get_changes_by_type(self, change_type):
        """Возвращает изменения по типу"""
        return [change for change in self.detailed_changes 
                if change.get('type') == change_type]


class Change(models.Model):
    """
    Модель для хранения отдельных изменений
    """
    CHANGE_TYPES = [
        ('added', 'Добавлено'),
        ('removed', 'Удалено'),
        ('modified', 'Изменено'),
        ('moved', 'Перемещено'),
    ]
    
    CHANGE_LOCATIONS = [
        ('text', 'Текст'),
        ('table', 'Таблица'),
        ('section', 'Раздел'),
        ('header', 'Заголовок'),
        ('structure', 'Структура'),
    ]
    
    comparison = models.ForeignKey(
        Comparison,
        on_delete=models.CASCADE,
        related_name='changes',
        verbose_name='Сравнение'
    )
    
    change_type = models.CharField(
        max_length=20,
        choices=CHANGE_TYPES,
        verbose_name='Тип изменения'
    )
    
    location = models.CharField(
        max_length=20,
        choices=CHANGE_LOCATIONS,
        verbose_name='Местоположение'
    )
    
    section = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Раздел'
    )
    
    old_value = models.TextField(
        blank=True,
        verbose_name='Старое значение'
    )
    
    new_value = models.TextField(
        blank=True,
        verbose_name='Новое значение'
    )
    
    confidence = models.FloatField(
        default=1.0,
        verbose_name='Уверенность (0-1)'
    )
    
    context = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Контекст изменения'
    )
    
    class Meta:
        verbose_name = 'Изменение'
        verbose_name_plural = 'Изменения'
        ordering = ['comparison', 'section', 'change_type']
    
    def __str__(self):
        return f"{self.get_change_type_display()} в {self.get_location_display()}: {self.section}"


class AnalysisSettings(models.Model):
    """
    Модель для настроек анализа
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='analysis_settings',
        verbose_name='Пользователь'
    )
    
    sensitivity = models.FloatField(
        default=0.8,
        verbose_name='Чувствительность к изменениям (0-1)'
    )
    
    include_text_changes = models.BooleanField(
        default=True,
        verbose_name='Анализировать изменения текста'
    )
    
    include_table_changes = models.BooleanField(
        default=True,
        verbose_name='Анализировать изменения таблиц'
    )
    
    include_structure_changes = models.BooleanField(
        default=True,
        verbose_name='Анализировать структурные изменения'
    )
    
    min_change_length = models.PositiveIntegerField(
        default=3,
        verbose_name='Минимальная длина изменения'
    )
    
    class Meta:
        verbose_name = 'Настройка анализа'
        verbose_name_plural = 'Настройки анализа'
        unique_together = ['user']
    
    def __str__(self):
        return f"Настройки анализа для {self.user.username}"