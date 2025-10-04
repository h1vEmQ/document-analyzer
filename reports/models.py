from django.db import models
from django.contrib.auth import get_user_model
from analysis.models import Comparison

User = get_user_model()


class Report(models.Model):
    """
    Модель для хранения сгенерированных отчетов
    """
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word'),
        ('html', 'HTML'),
    ]
    
    STATUS_CHOICES = [
        ('generating', 'Генерируется'),
        ('ready', 'Готов'),
        ('sent', 'Отправлен'),
        ('error', 'Ошибка'),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name='Название отчета'
    )
    
    comparison = models.ForeignKey(
        Comparison,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Сравнение'
    )
    
    format = models.CharField(
        max_length=10,
        choices=FORMAT_CHOICES,
        default='pdf',
        verbose_name='Формат'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='generating',
        verbose_name='Статус'
    )
    
    file = models.FileField(
        upload_to='reports/%Y/%m/%d/',
        null=True,
        blank=True,
        verbose_name='Файл отчета'
    )
    
    generated_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата генерации'
    )
    
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата отправки'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name='Пользователь'
    )
    
    # Версионирование отчетов
    parent_report = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='versions',
        verbose_name='Родительский отчет'
    )
    
    version = models.CharField(
        max_length=20,
        default='1.0',
        verbose_name='Версия отчета'
    )
    
    is_latest_version = models.BooleanField(
        default=True,
        verbose_name='Последняя версия'
    )
    
    version_notes = models.TextField(
        blank=True,
        verbose_name='Заметки к версии'
    )
    
    # Настройки генерации
    template_used = models.CharField(
        max_length=100,
        default='default',
        verbose_name='Использованный шаблон'
    )
    
    include_summary = models.BooleanField(
        default=True,
        verbose_name='Включить сводку'
    )
    
    include_details = models.BooleanField(
        default=True,
        verbose_name='Включить детали'
    )
    
    include_tables = models.BooleanField(
        default=True,
        verbose_name='Включить таблицы'
    )
    
    # Email настройки
    email_sent = models.BooleanField(
        default=False,
        verbose_name='Email отправлен'
    )
    
    email_recipients = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Получатели email'
    )
    
    # Метаданные отчета
    summary_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Данные сводки'
    )
    
    generation_time = models.FloatField(
        null=True,
        blank=True,
        verbose_name='Время генерации (сек)'
    )
    
    file_size = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name='Размер файла (байт)'
    )
    
    class Meta:
        verbose_name = 'Отчет'
        verbose_name_plural = 'Отчеты'
        ordering = ['-generated_date']
    
    def __str__(self):
        return f"{self.title} ({self.get_format_display()}) v{self.version}"
    
    def get_file_size_mb(self):
        """Возвращает размер файла в МБ"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_version_history(self):
        """Возвращает историю версий отчета"""
        if self.parent_report:
            # Если это версия другого отчета, возвращаем историю родительского
            root_report = self.get_root_report()
            # Включаем корневой отчет и все его версии
            from django.db.models import Q
            return Report.objects.filter(
                Q(id=root_report.id) | Q(parent_report=root_report)
            ).order_by('-generated_date')
        else:
            # Если это родительский отчет, возвращаем свою историю включая себя
            from django.db.models import Q
            return Report.objects.filter(
                Q(id=self.id) | Q(parent_report=self)
            ).order_by('-generated_date')
    
    def get_latest_version(self):
        """Возвращает последнюю версию отчета"""
        if self.parent_report:
            return self.parent_report.versions.filter(is_latest_version=True).first()
        else:
            return self.versions.filter(is_latest_version=True).first() or self
    
    def get_root_report(self):
        """Возвращает корневой отчет (первую версию)"""
        if self.parent_report:
            return self.parent_report.get_root_report()
        else:
            return self
    
    def create_new_version(self, new_file, version_notes=''):
        """Создает новую версию отчета"""
        # Получаем корневой отчет
        root_report = self.get_root_report()
        
        # Получаем следующий номер версии
        latest_version = root_report.get_latest_version()
        if latest_version:
            current_version = latest_version.version
            try:
                # Пытаемся увеличить номер версии
                version_parts = current_version.split('.')
                if len(version_parts) == 2:
                    major, minor = version_parts
                    new_version = f"{major}.{int(minor) + 1}"
                else:
                    new_version = f"{current_version}.1"
            except (ValueError, IndexError):
                new_version = "1.1"
        else:
            new_version = "1.1"
        
        # Помечаем текущую версию как не последнюю
        if latest_version:
            latest_version.is_latest_version = False
            latest_version.save()
        
        # Создаем новую версию
        new_report = Report.objects.create(
            title=self.title,
            comparison=self.comparison,
            format=self.format,
            file=new_file,
            user=self.user,
            version=new_version,
            parent_report=root_report,
            is_latest_version=True,
            version_notes=version_notes,
            template_used=self.template_used,
            include_summary=self.include_summary,
            include_details=self.include_details,
            include_tables=self.include_tables,
            summary_data=self.summary_data,
            status='ready'
        )
        
        return new_report
    
    def get_version_count(self):
        """Возвращает количество версий отчета"""
        return self.get_version_history().count()


class ReportTemplate(models.Model):
    """
    Модель для шаблонов отчетов
    """
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Название шаблона'
    )
    
    description = models.TextField(
        blank=True,
        verbose_name='Описание'
    )
    
    format = models.CharField(
        max_length=10,
        choices=Report.FORMAT_CHOICES,
        default='pdf',
        verbose_name='Формат'
    )
    
    template_content = models.TextField(
        verbose_name='Содержимое шаблона'
    )
    
    is_default = models.BooleanField(
        default=False,
        verbose_name='Шаблон по умолчанию'
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name='Активный'
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates',
        verbose_name='Создал'
    )
    
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    class Meta:
        verbose_name = 'Шаблон отчета'
        verbose_name_plural = 'Шаблоны отчетов'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_format_display()})"


class EmailNotification(models.Model):
    """
    Модель для уведомлений по email
    """
    STATUS_CHOICES = [
        ('pending', 'Ожидает отправки'),
        ('sent', 'Отправлено'),
        ('failed', 'Ошибка отправки'),
    ]
    
    report = models.ForeignKey(
        Report,
        on_delete=models.CASCADE,
        related_name='email_notifications',
        verbose_name='Отчет'
    )
    
    recipient_email = models.EmailField(
        verbose_name='Email получателя'
    )
    
    recipient_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Имя получателя'
    )
    
    subject = models.CharField(
        max_length=255,
        verbose_name='Тема письма'
    )
    
    message = models.TextField(
        verbose_name='Сообщение'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата отправки'
    )
    
    error_message = models.TextField(
        blank=True,
        verbose_name='Сообщение об ошибке'
    )
    
    class Meta:
        verbose_name = 'Email уведомление'
        verbose_name_plural = 'Email уведомления'
        ordering = ['-sent_date']
    
    def __str__(self):
        return f"Email для {self.recipient_email} - {self.report.title}"