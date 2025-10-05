from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django import forms
from .models import ApplicationSettings

User = get_user_model()

# Импортируем кастомную админ-панель
from .admin_site import admin_site


class ApplicationSettingsForm(forms.ModelForm):
    """Кастомная форма для настроек приложения"""
    
    class Meta:
        model = ApplicationSettings
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        # Извлекаем user из kwargs если он есть
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Настраиваем поле модели по умолчанию
        try:
            # Получаем доступные модели из Ollama
            from analysis.ollama_service import OllamaService
            ollama_service = OllamaService()
            
            if ollama_service.is_available():
                available_models = ollama_service.get_available_models()
                
                # Создаем choices для поля
                model_choices = []
                for model in available_models:
                    # Маппинг технических названий на читаемые
                    model_display_names = {
                        'llama3': 'Llama 3',
                        'llama3.1': 'Llama 3.1',
                        'llama3:latest': 'Llama 3',
                        'llama3.1:latest': 'Llama 3.1',
                        'mistral': 'Mistral',
                        'mistral:latest': 'Mistral',
                        'codellama': 'Code Llama',
                        'codellama:latest': 'Code Llama',
                        'deepseek-r1:7b': 'DeepSeek R1 7B',
                        'deepseek-r1:8b': 'DeepSeek R1 8B',
                    }
                    display_name = model_display_names.get(model, model)
                    model_choices.append((model, display_name))
                
                # Всегда заменяем CharField на ChoiceField
                if model_choices:
                    self.fields['default_neural_network_model'] = forms.ChoiceField(
                        choices=model_choices,
                        label='Модель нейросети по умолчанию',
                        help_text='Выберите модель нейросети по умолчанию для анализа документов'
                    )
                else:
                    # Если модели не найдены, показываем поле с пустыми вариантами
                    self.fields['default_neural_network_model'] = forms.ChoiceField(
                        choices=[('', 'Модели не найдены')],
                        label='Модель нейросети по умолчанию',
                        help_text='Модели не установлены в Ollama. Установите модели в Ollama для выбора.',
                        required=False
                    )
            else:
                # Если Ollama недоступен, показываем поле с информационным сообщением
                self.fields['default_neural_network_model'] = forms.ChoiceField(
                    choices=[('', 'Ollama недоступен')],
                    label='Модель нейросети по умолчанию',
                    help_text='Ollama сервис недоступен. Запустите Ollama для выбора модели.',
                    required=False
                )
                
        except Exception as e:
            # В случае ошибки показываем поле с информацией об ошибке
            self.fields['default_neural_network_model'] = forms.ChoiceField(
                choices=[('', 'Ошибка получения моделей')],
                label='Модель нейросети по умолчанию',
                help_text=f'Ошибка получения моделей: {str(e)}',
                required=False
            )


@admin.register(ApplicationSettings)
class ApplicationSettingsAdmin(admin.ModelAdmin):
    """Админ-класс для настроек приложения"""
    
    # Используем кастомную форму
    form = ApplicationSettingsForm
    
    def get_form(self, request, obj=None, **kwargs):
        """Переопределяем метод для передачи user в форму"""
        form = super().get_form(request, obj, **kwargs)
        
        # Создаем обертку для формы, которая передает user
        class FormWithUser(form):
            def __init__(self, *args, **kwargs):
                kwargs['user'] = request.user
                super().__init__(*args, **kwargs)
        
        return FormWithUser
    
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
            'fields': ('auto_analysis_enabled', 'analysis_timeout', 'default_neural_network_model'),
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
            settings.app_name = '📊 Анализатор документов'
            settings.app_description = 'Система анализа документов'
            settings.max_file_size = 10485760
            settings.allowed_file_types = 'docx,pdf'
            settings.auto_analysis_enabled = True
            settings.analysis_timeout = 300
            settings.default_neural_network_model = 'llama3'
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


# Кастомная админ-панель настроек удалена - используется admin_site.py

# Импортируем кастомную админ-панель
from .admin_site import admin_site