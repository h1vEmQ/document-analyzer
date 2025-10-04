from django.contrib import admin
from .models import Document, DocumentSection, DocumentTable


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    """
    Админ-панель для модели документов
    """
    list_display = ('title', 'filename', 'version', 'status', 'user', 'upload_date', 'file_size')
    list_filter = ('status', 'version', 'upload_date', 'user__role')
    search_fields = ('title', 'filename', 'user__username', 'user__email')
    readonly_fields = ('checksum', 'file_size', 'upload_date', 'processed_date')
    ordering = ('-upload_date',)
    
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'filename', 'file', 'version', 'status')}),
        ('Пользователь', {'fields': ('user',)}),
        ('Системная информация', {'fields': ('file_size', 'checksum', 'upload_date', 'processed_date')}),
        ('Содержимое', {'fields': ('content_text', 'content_structure', 'metadata')}),
    )
    
    def get_file_size_mb(self, obj):
        """Отображает размер файла в МБ"""
        if obj.file_size:
            return f"{round(obj.file_size / (1024 * 1024), 2)} МБ"
        return "0 МБ"
    get_file_size_mb.short_description = 'Размер файла'


@admin.register(DocumentSection)
class DocumentSectionAdmin(admin.ModelAdmin):
    """
    Админ-панель для разделов документа
    """
    list_display = ('title', 'document', 'level', 'order')
    list_filter = ('level', 'document__status')
    search_fields = ('title', 'content', 'document__title')
    ordering = ('document', 'order')


@admin.register(DocumentTable)
class DocumentTableAdmin(admin.ModelAdmin):
    """
    Админ-панель для таблиц документа
    """
    list_display = ('title', 'document', 'order')
    list_filter = ('document__status',)
    search_fields = ('title', 'document__title')
    ordering = ('document', 'order')