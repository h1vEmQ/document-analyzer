from django.contrib import admin
from .models import Report, ReportTemplate, EmailNotification


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """
    Админ-панель для отчетов
    """
    list_display = ('title', 'comparison', 'format', 'status', 'user', 'generated_date', 'get_file_size_mb')
    list_filter = ('format', 'status', 'generated_date', 'user__role')
    search_fields = ('title', 'comparison__title', 'user__username')
    readonly_fields = ('generated_date', 'sent_date', 'generation_time', 'file_size')
    ordering = ('-generated_date',)
    
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'comparison', 'format', 'status')}),
        ('Пользователь', {'fields': ('user',)}),
        ('Файл', {'fields': ('file', 'file_size')}),
        ('Временные метки', {'fields': ('generated_date', 'sent_date', 'generation_time')}),
        ('Настройки генерации', {'fields': (
            'template_used', 
            'include_summary', 
            'include_details', 
            'include_tables'
        )}),
        ('Email настройки', {'fields': ('email_sent', 'email_recipients')}),
        ('Данные', {'fields': ('summary_data',)}),
    )
    
    def get_file_size_mb(self, obj):
        """Отображает размер файла в МБ"""
        return obj.get_file_size_mb()
    get_file_size_mb.short_description = 'Размер файла (МБ)'


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    """
    Админ-панель для шаблонов отчетов
    """
    list_display = ('name', 'format', 'is_default', 'is_active', 'created_by', 'created_date')
    list_filter = ('format', 'is_default', 'is_active', 'created_date')
    search_fields = ('name', 'description', 'created_by__username')
    readonly_fields = ('created_date',)
    ordering = ('name',)
    
    fieldsets = (
        ('Основная информация', {'fields': ('name', 'description', 'format')}),
        ('Шаблон', {'fields': ('template_content',)}),
        ('Настройки', {'fields': ('is_default', 'is_active')}),
        ('Автор', {'fields': ('created_by', 'created_date')}),
    )


@admin.register(EmailNotification)
class EmailNotificationAdmin(admin.ModelAdmin):
    """
    Админ-панель для email уведомлений
    """
    list_display = ('report', 'recipient_email', 'status', 'sent_date')
    list_filter = ('status', 'sent_date', 'report__format')
    search_fields = ('recipient_email', 'recipient_name', 'report__title', 'subject')
    readonly_fields = ('sent_date',)
    ordering = ('-sent_date',)
    
    fieldsets = (
        ('Основная информация', {'fields': ('report', 'status')}),
        ('Получатель', {'fields': ('recipient_email', 'recipient_name')}),
        ('Сообщение', {'fields': ('subject', 'message')}),
        ('Результат', {'fields': ('sent_date', 'error_message')}),
    )