from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from .models import ApplicationSettings

User = get_user_model()

# Импортируем кастомную админ-панель
from .admin_site import admin_site


@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(admin.ModelAdmin):
    """Админ-класс для настроек приложения"""
    
    # Настройки отображения в списке
    list_display = [
        'app_name',
        'auto_analysis_status',
        'auto_reports_status',
        'email_notifications_status',
        'updated_at',
        'updated_by_display'
    ]
    
    # Поля только для чтения
    readonly_fields = ['created_at', 'updated_at', 'updated_by']
    
    # Группировка полей
    fieldsets = (
        ('Основные настройки', {
            'fields': ('app_name', 'app_description')
        }),
        ('Настройки документов', {
            'fields': ('max_file_size', 'allowed_file_types'),
            'classes': ('collapse',)
        }),
        ('Настройки анализа', {
            'fields': ('auto_analysis_enabled', 'analysis_timeout'),
            'classes': ('collapse',)
        }),
        ('Настройки отчетов', {
            'fields': ('auto_reports_enabled', 'default_report_format'),
            'classes': ('collapse',)
        }),
        ('Настройки уведомлений', {
            'fields': ('email_notifications_enabled', 'notification_email'),
            'classes': ('collapse',)
        }),
        ('Настройки безопасности', {
            'fields': ('session_timeout', 'max_login_attempts'),
            'classes': ('collapse',)
        }),
        ('Мета-информация', {
            'fields': ('created_at', 'updated_at', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    # Настройки отображения полей
    def auto_analysis_status(self, obj):
        """Отображение статуса автоматического анализа"""
        if obj.auto_analysis_enabled:
            return format_html('<span style="color: green;">✓ Включен</span>')
        return format_html('<span style="color: red;">✗ Выключен</span>')
    auto_analysis_status.short_description = 'Автоанализ'
    
    def auto_reports_status(self, obj):
        """Отображение статуса автоматических отчетов"""
        if obj.auto_reports_enabled:
            return format_html('<span style="color: green;">✓ Включен</span>')
        return format_html('<span style="color: red;">✗ Выключен</span>')
    auto_reports_status.short_description = 'Автоотчеты'
    
    def email_notifications_status(self, obj):
        """Отображение статуса email уведомлений"""
        if obj.email_notifications_enabled:
            return format_html('<span style="color: green;">✓ Включены</span>')
        return format_html('<span style="color: red;">✗ Выключены</span>')
    email_notifications_status.short_description = 'Email уведомления'
    
    def updated_by_display(self, obj):
        """Отображение пользователя, обновившего настройки"""
        if obj.updated_by:
            return obj.updated_by.username
        return '-'
    updated_by_display.short_description = 'Обновлено пользователем'
    
    # Переопределяем save для автоматического указания пользователя
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    # Настройки интерфейса
    def has_add_permission(self, request):
        """Запретить добавление новых записей (только одна запись настроек)"""
        return not ApplicationSettings.objects.exists()
    
    def changelist_view(self, request, extra_context=None):
        """Кастомный вид списка настроек"""
        extra_context = extra_context or {}
        settings = ApplicationSettings.get_settings()
        extra_context['settings'] = settings
        return super().changelist_view(request, extra_context)
    
    # Добавляем кнопки действий
    actions = ['reset_to_defaults']
    
    def reset_to_defaults(self, request, queryset):
        """Сброс настроек к значениям по умолчанию"""
        for settings in queryset:
            settings.app_name = 'WARA'
            settings.app_description = 'Система анализа документов'
            settings.max_file_size = 10485760
            settings.allowed_file_types = 'docx,pdf'
            settings.auto_analysis_enabled = True
            settings.analysis_timeout = 300
            settings.auto_reports_enabled = True
            settings.default_report_format = 'pdf'
            settings.email_notifications_enabled = False
            settings.notification_email = ''
            settings.session_timeout = 3600
            settings.max_login_attempts = 5
            settings.updated_by = request.user
            settings.save()
        
        self.message_user(
            request,
            f'Настройки сброшены к значениям по умолчанию для {queryset.count()} записи(ей).'
        )
    reset_to_defaults.short_description = 'Сбросить к значениям по умолчанию'


# Кастомная админ-страница для настроек
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import render
from django.urls import path
from django.contrib.admin import AdminSite


class ApplicationSettingsChangeList(ChangeList):
    """Кастомный список настроек"""
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = ApplicationSettings.get_settings()
        return context


# Добавляем кастомную страницу настроек в админ-панель
class WARAAdminSite(AdminSite):
    """Кастомная админ-панель WARA"""
    
    site_header = 'WARA Админ-панель'
    site_title = 'WARA'
    index_title = 'Управление системой'
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('settings/', self.admin_view(self.settings_view), name='settings'),
        ]
        return custom_urls + urls
    
    def settings_view(self, request):
        """Кастомное представление страницы настроек"""
        settings = ApplicationSettings.get_settings()
        
        if request.method == 'POST':
            # Обработка формы настроек
            settings.app_name = request.POST.get('app_name', settings.app_name)
            settings.app_description = request.POST.get('app_description', settings.app_description)
            settings.max_file_size = int(request.POST.get('max_file_size', settings.max_file_size))
            settings.allowed_file_types = request.POST.get('allowed_file_types', settings.allowed_file_types)
            settings.auto_analysis_enabled = request.POST.get('auto_analysis_enabled') == 'on'
            settings.analysis_timeout = int(request.POST.get('analysis_timeout', settings.analysis_timeout))
            settings.auto_reports_enabled = request.POST.get('auto_reports_enabled') == 'on'
            settings.default_report_format = request.POST.get('default_report_format', settings.default_report_format)
            settings.email_notifications_enabled = request.POST.get('email_notifications_enabled') == 'on'
            settings.notification_email = request.POST.get('notification_email', settings.notification_email)
            settings.session_timeout = int(request.POST.get('session_timeout', settings.session_timeout))
            settings.max_login_attempts = int(request.POST.get('max_login_attempts', settings.max_login_attempts))
            settings.updated_by = request.user
            settings.save()
            
            messages.success(request, 'Настройки успешно сохранены!')
        
        context = {
            'settings': settings,
            'title': 'Настройки приложения',
            'site_header': self.site_header,
            'site_title': self.site_title,
            'has_permission': True,
        }
        
        return render(request, 'admin/settings.html', context)