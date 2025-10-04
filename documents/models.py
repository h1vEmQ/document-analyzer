from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import hashlib
import os

User = get_user_model()


class Document(models.Model):
    """
    Модель для хранения документов Word (.docx)
    """
    STATUS_CHOICES = [
        ('uploaded', 'Загружен'),
        ('processing', 'Обрабатывается'),
        ('processed', 'Обработан'),
        ('error', 'Ошибка'),
    ]
    
    title = models.CharField(
        max_length=255,
        verbose_name='Название документа'
    )
    
    filename = models.CharField(
        max_length=255,
        verbose_name='Имя файла'
    )
    
    file = models.FileField(
        upload_to='documents/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['docx'])],
        verbose_name='Файл документа'
    )
    
    file_size = models.BigIntegerField(
        verbose_name='Размер файла (байт)'
    )
    
    checksum = models.CharField(
        max_length=64,
        verbose_name='Контрольная сумма'
    )
    
    version = models.CharField(
        max_length=50,
        default='1.0',
        verbose_name='Версия'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='uploaded',
        verbose_name='Статус'
    )
    
    upload_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата загрузки'
    )
    
    processed_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата обработки'
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name='Пользователь'
    )
    
    # Версионирование
    parent_document = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='versions',
        verbose_name='Родительский документ'
    )
    
    is_latest_version = models.BooleanField(
        default=True,
        verbose_name='Последняя версия'
    )
    
    version_notes = models.TextField(
        blank=True,
        verbose_name='Заметки к версии'
    )
    
    # Извлеченное содержимое
    content_text = models.TextField(
        blank=True,
        verbose_name='Текстовое содержимое'
    )
    
    content_structure = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Структура документа'
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Метаданные'
    )
    
    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'
        ordering = ['-upload_date']
    
    def __str__(self):
        return f"{self.title} (v{self.version})"
    
    def save(self, *args, **kwargs):
        if self.file and not self.checksum:
            # Вычисляем контрольную сумму файла
            self.checksum = self.calculate_checksum()
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    def get_version_history(self):
        """Возвращает историю версий документа"""
        if self.parent_document:
            # Если это версия другого документа, возвращаем историю родительского
            root_doc = self.get_root_document()
            # Включаем корневой документ и все его версии
            from django.db.models import Q
            return Document.objects.filter(
                Q(id=root_doc.id) | Q(parent_document=root_doc)
            ).order_by('-upload_date')
        else:
            # Если это родительский документ, возвращаем свою историю включая себя
            from django.db.models import Q
            return Document.objects.filter(
                Q(id=self.id) | Q(parent_document=self)
            ).order_by('-upload_date')
    
    def get_latest_version(self):
        """Возвращает последнюю версию документа"""
        if self.parent_document:
            return self.parent_document.versions.filter(is_latest_version=True).first()
        else:
            return self.versions.filter(is_latest_version=True).first() or self
    
    def get_root_document(self):
        """Возвращает корневой документ (первую версию)"""
        if self.parent_document:
            return self.parent_document.get_root_document()
        else:
            return self
    
    def create_new_version(self, new_file, version_notes=''):
        """Создает новую версию документа"""
        # Получаем корневой документ
        root_doc = self.get_root_document()
        
        # Получаем следующий номер версии
        latest_version = root_doc.get_latest_version()
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
        new_doc = Document.objects.create(
            title=self.title,
            filename=new_file.name,
            file=new_file,
            user=self.user,
            version=new_version,
            parent_document=root_doc,
            is_latest_version=True,
            version_notes=version_notes
        )
        
        return new_doc
    
    def get_version_count(self):
        """Возвращает количество версий документа"""
        return self.get_version_history().count()
    
    def calculate_checksum(self):
        """Вычисляет SHA-256 контрольную сумму файла"""
        if not self.file:
            return ''
        
        hash_sha256 = hashlib.sha256()
        self.file.seek(0)
        for chunk in iter(lambda: self.file.read(4096), b""):
            hash_sha256.update(chunk)
        self.file.seek(0)
        return hash_sha256.hexdigest()
    
    def get_file_extension(self):
        """Возвращает расширение файла"""
        return os.path.splitext(self.filename)[1].lower()
    
    def is_docx(self):
        """Проверяет, является ли файл .docx"""
        return self.get_file_extension() == '.docx'
    
    def get_file_size_mb(self):
        """Возвращает размер файла в МБ"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_parsed_sections_count(self):
        """Возвращает количество извлеченных разделов"""
        return self.sections.count()
    
    def get_parsed_tables_count(self):
        """Возвращает количество извлеченных таблиц"""
        return self.tables.count()
    
    def has_content(self):
        """Проверяет, есть ли извлеченное содержимое"""
        return bool(self.content_text and self.content_text.strip())
    
    def get_content_text(self):
        """Возвращает извлеченное текстовое содержимое документа"""
        return self.content_text or ""


class DocumentSection(models.Model):
    """
    Модель для хранения разделов документа
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name='Документ'
    )
    
    title = models.CharField(
        max_length=255,
        verbose_name='Заголовок раздела'
    )
    
    content = models.TextField(
        verbose_name='Содержимое раздела'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    
    level = models.PositiveIntegerField(
        default=1,
        verbose_name='Уровень заголовка'
    )
    
    class Meta:
        verbose_name = 'Раздел документа'
        verbose_name_plural = 'Разделы документа'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.document.title} - {self.title}"


class DocumentTable(models.Model):
    """
    Модель для хранения таблиц из документа
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='tables',
        verbose_name='Документ'
    )
    
    title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='Заголовок таблицы'
    )
    
    data = models.JSONField(
        verbose_name='Данные таблицы'
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='Порядок'
    )
    
    class Meta:
        verbose_name = 'Таблица документа'
        verbose_name_plural = 'Таблицы документа'
        ordering = ['order']
    
    def __str__(self):
        return f"{self.document.title} - {self.title or 'Таблица'}"