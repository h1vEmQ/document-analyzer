from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.db.models import Q
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
    
    processing_error = models.TextField(
        blank=True,
        verbose_name='Ошибка обработки'
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
    
    # Ключевые моменты документа
    key_points = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Ключевые моменты'
    )
    
    key_points_generated_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Дата генерации ключевых моментов'
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
    
    def get_versions_with_key_points(self):
        """Возвращает версии документа с ключевыми моментами"""
        return self.get_version_history().filter(
            Q(key_points__isnull=False) & ~Q(key_points=[])
        )
    
    def get_latest_version(self):
        """Возвращает последнюю версию документа"""
        if self.parent_document:
            # Если это версия, возвращаем последнюю версию родительского документа
            return self.parent_document.get_latest_version()
        else:
            # Если это корневой документ, ищем последнюю версию
            latest = self.versions.filter(is_latest_version=True).first()
            return latest if latest else self
    
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
    
    def has_key_points(self):
        """Проверяет, есть ли сгенерированные ключевые моменты"""
        return bool(self.key_points and len(self.key_points) > 0)
    
    def get_key_points(self):
        """Возвращает ключевые моменты документа"""
        return self.key_points or []
    
    def get_key_points_summary(self):
        """Возвращает краткое резюме из ключевых моментов"""
        if not self.has_key_points():
            return ""
        
        # Ищем резюме в ключевых моментах
        for point in self.key_points:
            if isinstance(point, dict) and 'summary' in point:
                return point['summary']
        
        return ""
    
    def get_next_version(self):
        """Возвращает следующий номер версии для документа"""
        try:
            # Получаем все версии этого документа
            versions = Document.objects.filter(
                Q(id=self.id) | Q(parent_document=self.id) | Q(parent_document=self.parent_document)
            ).exclude(id=self.id).order_by('version')
            
            if not versions.exists():
                # Если это первая версия, возвращаем 2.0
                return '2.0'
            
            # Парсим версии и находим максимальную
            max_version = 1.0
            for doc in versions:
                try:
                    version_parts = doc.version.split('.')
                    if len(version_parts) == 2:
                        major, minor = int(version_parts[0]), int(version_parts[1])
                        version_num = major + (minor / 10.0)
                        max_version = max(max_version, version_num)
                except (ValueError, IndexError):
                    continue
            
            # Увеличиваем версию на 0.1
            next_version = max_version + 0.1
            major = int(next_version)
            minor = int((next_version - major) * 10)
            return f"{major}.{minor}"
            
        except Exception:
            # В случае ошибки возвращаем простую инкрементальную версию
            version_count = self.get_version_count()
            return f"{version_count + 1}.0"


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


class DocumentTableAnalysis(models.Model):
    """
    Модель для хранения анализа таблиц документа
    """
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='table_analyses',
        verbose_name='Документ'
    )
    
    table = models.ForeignKey(
        DocumentTable,
        on_delete=models.CASCADE,
        related_name='analyses',
        verbose_name='Таблица',
        null=True,
        blank=True
    )
    
    # Основные метрики таблицы
    row_count = models.PositiveIntegerField(
        verbose_name='Количество строк'
    )
    
    column_count = models.PositiveIntegerField(
        verbose_name='Количество столбцов'
    )
    
    cell_count = models.PositiveIntegerField(
        verbose_name='Общее количество ячеек'
    )
    
    # Анализ содержимого
    empty_cells_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество пустых ячеек'
    )
    
    numeric_cells_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество числовых ячеек'
    )
    
    text_cells_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество текстовых ячеек'
    )
    
    # Структурный анализ
    has_headers = models.BooleanField(
        default=False,
        verbose_name='Есть заголовки'
    )
    
    header_row_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество строк заголовков'
    )
    
    # Семантический анализ
    table_type = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Тип таблицы'
    )
    
    main_topic = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='Основная тема'
    )
    
    key_metrics = models.JSONField(
        default=list,
        blank=True,
        verbose_name='Ключевые метрики'
    )
    
    # Временные метки
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Анализ таблицы'
        verbose_name_plural = 'Анализы таблиц'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Анализ таблицы {self.table.title if self.table else 'N/A'} в документе {self.document.title}"
    
    def get_fill_percentage(self):
        """Возвращает процент заполненности таблицы"""
        if self.cell_count == 0:
            return 0
        filled_cells = self.cell_count - self.empty_cells_count
        return round((filled_cells / self.cell_count) * 100, 2)
    
    def get_numeric_percentage(self):
        """Возвращает процент числовых ячеек"""
        if self.cell_count == 0:
            return 0
        return round((self.numeric_cells_count / self.cell_count) * 100, 2)
    
    def get_text_percentage(self):
        """Возвращает процент текстовых ячеек"""
        if self.cell_count == 0:
            return 0
        return round((self.text_cells_count / self.cell_count) * 100, 2)