from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ApplicationSettings(models.Model):
    """Модель для хранения настроек приложения"""
    
    # Основные настройки приложения
    app_name = models.CharField(
        max_length=100, 
        default='Document analyzer',
        verbose_name='Название приложения'
    )
    app_description = models.TextField(
        default='Система анализа документов',
        verbose_name='Описание приложения'
    )
    
    # Настройки документов
    max_file_size = models.PositiveIntegerField(
        default=10485760,  # 10MB
        verbose_name='Максимальный размер файла (байты)'
    )
    allowed_file_types = models.TextField(
        default='docx,pdf',
        verbose_name='Разрешенные типы файлов (через запятую)'
    )
    
    # Настройки анализа
    auto_analysis_enabled = models.BooleanField(
        default=True,
        verbose_name='Автоматический анализ включен'
    )
    analysis_timeout = models.PositiveIntegerField(
        default=300,  # 5 минут
        verbose_name='Таймаут анализа (секунды)'
    )
    
    # Настройки отчетов
    auto_reports_enabled = models.BooleanField(
        default=True,
        verbose_name='Автоматическая генерация отчетов включена'
    )
    default_report_format = models.CharField(
        max_length=10,
        choices=[('pdf', 'PDF'), ('docx', 'DOCX')],
        default='pdf',
        verbose_name='Формат отчета по умолчанию'
    )
    
    # Настройки интерфейса
    items_per_page = models.PositiveIntegerField(
        default=10,
        verbose_name='Количество элементов на странице'
    )
    
    # Настройки уведомлений
    email_notifications_enabled = models.BooleanField(
        default=False,
        verbose_name='Email уведомления включены'
    )
    notification_email = models.EmailField(
        blank=True,
        verbose_name='Email для уведомлений'
    )
    
    # Настройки безопасности
    session_timeout = models.PositiveIntegerField(
        default=3600,  # 1 час
        verbose_name='Таймаут сессии (секунды)'
    )
    max_login_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name='Максимальное количество попыток входа'
    )
    
    # Мета-информация
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Обновлено пользователем'
    )
    
    class Meta:
        verbose_name = 'Настройки приложения'
        verbose_name_plural = 'Настройки приложения'
    
    def __str__(self):
        return f'Настройки {self.app_name}'
    
    def save(self, *args, **kwargs):
        # Убеждаемся, что существует только одна запись настроек
        if not self.pk and ApplicationSettings.objects.exists():
            # Если уже есть настройки, обновляем их вместо создания новых
            existing = ApplicationSettings.objects.first()
            for field in self._meta.fields:
                if field.name not in ['id', 'created_at']:
                    setattr(existing, field.name, getattr(self, field.name))
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Получить настройки приложения (создать если не существует)"""
        settings, created = cls.objects.get_or_create(
            defaults={
                'app_name': 'Document analyzer',
                'app_description': 'Система анализа документов',
                'items_per_page': 10,
            }
        )
        return settings


class ServerSettings(models.Model):
    """Модель для настроек сервера"""
    
    # Основные настройки сервера
    server_name = models.CharField(
        max_length=100,
        default='Document analyzer Server',
        verbose_name='Название сервера'
    )
    
    server_description = models.TextField(
        default='Сервер системы анализа документов Document analyzer',
        verbose_name='Описание сервера'
    )
    
    # Настройки производительности
    max_concurrent_requests = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимальное количество одновременных запросов'
    )
    
    request_timeout = models.PositiveIntegerField(
        default=30,
        verbose_name='Таймаут запросов (секунды)'
    )
    
    max_memory_usage = models.PositiveIntegerField(
        default=2048,
        verbose_name='Максимальное использование памяти (МБ)'
    )
    
    # Настройки логирования
    log_level = models.CharField(
        max_length=10,
        choices=[
            ('DEBUG', 'DEBUG'),
            ('INFO', 'INFO'),
            ('WARNING', 'WARNING'),
            ('ERROR', 'ERROR'),
            ('CRITICAL', 'CRITICAL'),
        ],
        default='INFO',
        verbose_name='Уровень логирования'
    )
    
    log_retention_days = models.PositiveIntegerField(
        default=30,
        verbose_name='Срок хранения логов (дни)'
    )
    
    enable_access_log = models.BooleanField(
        default=True,
        verbose_name='Включить логирование доступа'
    )
    
    # Настройки кэширования
    enable_cache = models.BooleanField(
        default=True,
        verbose_name='Включить кэширование'
    )
    
    cache_timeout = models.PositiveIntegerField(
        default=300,
        verbose_name='Таймаут кэша (секунды)'
    )
    
    max_cache_size = models.PositiveIntegerField(
        default=100,
        verbose_name='Максимальный размер кэша (МБ)'
    )
    
    # Настройки безопасности
    enable_rate_limiting = models.BooleanField(
        default=True,
        verbose_name='Включить ограничение частоты запросов'
    )
    
    rate_limit_per_minute = models.PositiveIntegerField(
        default=60,
        verbose_name='Лимит запросов в минуту'
    )
    
    enable_csrf_protection = models.BooleanField(
        default=True,
        verbose_name='Включить защиту от CSRF'
    )
    
    session_cookie_secure = models.BooleanField(
        default=False,
        verbose_name='Безопасные cookies сессии'
    )
    
    # Настройки мониторинга
    enable_health_check = models.BooleanField(
        default=True,
        verbose_name='Включить проверку здоровья сервера'
    )
    
    health_check_interval = models.PositiveIntegerField(
        default=60,
        verbose_name='Интервал проверки здоровья (секунды)'
    )
    
    enable_metrics = models.BooleanField(
        default=True,
        verbose_name='Включить сбор метрик'
    )
    
    # Настройки резервного копирования
    enable_backup = models.BooleanField(
        default=True,
        verbose_name='Включить автоматическое резервное копирование'
    )
    
    backup_interval_hours = models.PositiveIntegerField(
        default=24,
        verbose_name='Интервал резервного копирования (часы)'
    )
    
    backup_retention_days = models.PositiveIntegerField(
        default=30,
        verbose_name='Срок хранения резервных копий (дни)'
    )
    
    # Мета-информация
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Создано')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Обновлено')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Обновлено пользователем'
    )
    
    class Meta:
        verbose_name = 'Настройки сервера'
        verbose_name_plural = 'Настройки сервера'
    
    def __str__(self):
        return f'Настройки сервера {self.server_name}'
    
    def save(self, *args, **kwargs):
        # Убеждаемся, что существует только одна запись настроек сервера
        if not self.pk and ServerSettings.objects.exists():
            # Если уже есть настройки, обновляем их вместо создания новых
            existing = ServerSettings.objects.first()
            for field in self._meta.fields:
                if field.name not in ['id', 'created_at']:
                    setattr(existing, field.name, getattr(self, field.name))
            existing.save()
            return existing
        return super().save(*args, **kwargs)
    
    @classmethod
    def get_settings(cls):
        """Получить настройки сервера (создать если не существует)"""
        settings, created = cls.objects.get_or_create(
            defaults={
                'server_name': 'Document analyzer Server',
                'server_description': 'Сервер системы анализа документов Document analyzer',
            }
        )
        return settings