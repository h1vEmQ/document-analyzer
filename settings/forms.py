from django import forms
from django.core.exceptions import ValidationError
from .models import ApplicationSettings, ServerSettings


class ApplicationSettingsForm(forms.ModelForm):
    """Форма для редактирования настроек приложения"""
    
    class Meta:
        model = ApplicationSettings
        fields = [
            'app_name',
            'app_description',
            'max_file_size',
            'allowed_file_types',
            'auto_analysis_enabled',
            'analysis_timeout',
            'auto_reports_enabled',
            'default_report_format',
            'email_notifications_enabled',
            'notification_email',
            'session_timeout',
            'max_login_attempts',
        ]
        widgets = {
            'app_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название приложения'
            }),
            'app_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите описание приложения'
            }),
            'max_file_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'step': '1024'
            }),
            'allowed_file_types': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'docx,pdf,txt'
            }),
            'analysis_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '3600'
            }),
            'default_report_format': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notification_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'example@domain.com'
            }),
            'session_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '300',
                'max': '86400'
            }),
            'max_login_attempts': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '10'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем CSS классы для чекбоксов
        self.fields['auto_analysis_enabled'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['auto_reports_enabled'].widget.attrs.update({'class': 'form-check-input'})
        self.fields['email_notifications_enabled'].widget.attrs.update({'class': 'form-check-input'})
    
    def clean_max_file_size(self):
        """Валидация максимального размера файла"""
        max_file_size = self.cleaned_data['max_file_size']
        if max_file_size < 1024:  # Минимум 1KB
            raise ValidationError('Максимальный размер файла должен быть не менее 1 КБ')
        if max_file_size > 104857600:  # Максимум 100MB
            raise ValidationError('Максимальный размер файла не должен превышать 100 МБ')
        return max_file_size
    
    def clean_allowed_file_types(self):
        """Валидация разрешенных типов файлов"""
        allowed_types = self.cleaned_data['allowed_file_types']
        if not allowed_types:
            raise ValidationError('Необходимо указать хотя бы один тип файла')
        
        # Проверяем формат (только буквы, цифры и запятые)
        import re
        if not re.match(r'^[a-zA-Z0-9,]+$', allowed_types):
            raise ValidationError('Типы файлов должны содержать только буквы, цифры и запятые')
        
        # Разделяем и проверяем каждый тип
        types_list = [t.strip().lower() for t in allowed_types.split(',')]
        valid_types = ['docx', 'pdf', 'txt', 'rtf', 'odt']
        
        for file_type in types_list:
            if file_type not in valid_types:
                raise ValidationError(f'Неподдерживаемый тип файла: {file_type}. '
                                    f'Поддерживаемые типы: {", ".join(valid_types)}')
        
        return allowed_types
    
    def clean_analysis_timeout(self):
        """Валидация таймаута анализа"""
        timeout = self.cleaned_data['analysis_timeout']
        if timeout < 1:
            raise ValidationError('Таймаут анализа должен быть не менее 1 секунды')
        if timeout > 3600:
            raise ValidationError('Таймаут анализа не должен превышать 1 час')
        return timeout
    
    def clean_session_timeout(self):
        """Валидация таймаута сессии"""
        timeout = self.cleaned_data['session_timeout']
        if timeout < 300:  # Минимум 5 минут
            raise ValidationError('Таймаут сессии должен быть не менее 5 минут')
        if timeout > 86400:  # Максимум 24 часа
            raise ValidationError('Таймаут сессии не должен превышать 24 часа')
        return timeout
    
    def clean_max_login_attempts(self):
        """Валидация максимального количества попыток входа"""
        attempts = self.cleaned_data['max_login_attempts']
        if attempts < 1:
            raise ValidationError('Максимальное количество попыток должно быть не менее 1')
        if attempts > 10:
            raise ValidationError('Максимальное количество попыток не должно превышать 10')
        return attempts
    
    def clean_notification_email(self):
        """Валидация email для уведомлений"""
        email = self.cleaned_data['notification_email']
        email_notifications_enabled = self.cleaned_data.get('email_notifications_enabled', False)
        
        if email_notifications_enabled and not email:
            raise ValidationError('Необходимо указать email для уведомлений')
        
        return email
    
    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        
        # Проверяем, что если включены email уведомления, то указан email
        email_notifications_enabled = cleaned_data.get('email_notifications_enabled')
        notification_email = cleaned_data.get('notification_email')
        
        if email_notifications_enabled and not notification_email:
            self.add_error('notification_email', 'Необходимо указать email для уведомлений')
        
        return cleaned_data


class QuickSettingsForm(forms.Form):
    """Быстрая форма для основных настроек"""
    
    app_name = forms.CharField(
        max_length=100,
        label='Название приложения',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'WARA'
        })
    )
    
    auto_analysis_enabled = forms.BooleanField(
        required=False,
        label='Автоматический анализ',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    auto_reports_enabled = forms.BooleanField(
        required=False,
        label='Автоматические отчеты',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    email_notifications_enabled = forms.BooleanField(
        required=False,
        label='Email уведомления',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings', None)
        super().__init__(*args, **kwargs)
        
        if settings:
            self.fields['app_name'].initial = settings.app_name
            self.fields['auto_analysis_enabled'].initial = settings.auto_analysis_enabled
            self.fields['auto_reports_enabled'].initial = settings.auto_reports_enabled
            self.fields['email_notifications_enabled'].initial = settings.email_notifications_enabled


class ServerSettingsForm(forms.ModelForm):
    """Форма для редактирования настроек сервера"""
    
    class Meta:
        model = ServerSettings
        fields = [
            'server_name',
            'server_description',
            'max_concurrent_requests',
            'request_timeout',
            'max_memory_usage',
            'log_level',
            'log_retention_days',
            'enable_access_log',
            'enable_cache',
            'cache_timeout',
            'max_cache_size',
            'enable_rate_limiting',
            'rate_limit_per_minute',
            'enable_csrf_protection',
            'session_cookie_secure',
            'enable_health_check',
            'health_check_interval',
            'enable_metrics',
            'enable_backup',
            'backup_interval_hours',
            'backup_retention_days',
        ]
        widgets = {
            'server_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название сервера'
            }),
            'server_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Введите описание сервера'
            }),
            'max_concurrent_requests': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'request_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '300'
            }),
            'max_memory_usage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '128',
                'max': '16384'
            }),
            'log_level': forms.Select(attrs={
                'class': 'form-control'
            }),
            'log_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '365'
            }),
            'cache_timeout': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '3600'
            }),
            'max_cache_size': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1024'
            }),
            'rate_limit_per_minute': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '1000'
            }),
            'health_check_interval': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '10',
                'max': '3600'
            }),
            'backup_interval_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '168'
            }),
            'backup_retention_days': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '365'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Добавляем CSS классы для чекбоксов
        checkbox_fields = [
            'enable_access_log', 'enable_cache', 'enable_rate_limiting',
            'enable_csrf_protection', 'session_cookie_secure',
            'enable_health_check', 'enable_metrics', 'enable_backup'
        ]
        
        for field_name in checkbox_fields:
            self.fields[field_name].widget.attrs.update({'class': 'form-check-input'})
    
    def clean_max_concurrent_requests(self):
        """Валидация максимального количества одновременных запросов"""
        value = self.cleaned_data['max_concurrent_requests']
        if value < 1:
            raise ValidationError('Количество одновременных запросов должно быть не менее 1')
        if value > 1000:
            raise ValidationError('Количество одновременных запросов не должно превышать 1000')
        return value
    
    def clean_request_timeout(self):
        """Валидация таймаута запросов"""
        value = self.cleaned_data['request_timeout']
        if value < 1:
            raise ValidationError('Таймаут запросов должен быть не менее 1 секунды')
        if value > 300:
            raise ValidationError('Таймаут запросов не должен превышать 300 секунд')
        return value
    
    def clean_max_memory_usage(self):
        """Валидация максимального использования памяти"""
        value = self.cleaned_data['max_memory_usage']
        if value < 128:
            raise ValidationError('Максимальное использование памяти должно быть не менее 128 МБ')
        if value > 16384:
            raise ValidationError('Максимальное использование памяти не должно превышать 16 ГБ')
        return value
    
    def clean_log_retention_days(self):
        """Валидация срока хранения логов"""
        value = self.cleaned_data['log_retention_days']
        if value < 1:
            raise ValidationError('Срок хранения логов должен быть не менее 1 дня')
        if value > 365:
            raise ValidationError('Срок хранения логов не должен превышать 365 дней')
        return value
    
    def clean_cache_timeout(self):
        """Валидация таймаута кэша"""
        value = self.cleaned_data['cache_timeout']
        if value < 1:
            raise ValidationError('Таймаут кэша должен быть не менее 1 секунды')
        if value > 3600:
            raise ValidationError('Таймаут кэша не должен превышать 1 час')
        return value
    
    def clean_max_cache_size(self):
        """Валидация максимального размера кэша"""
        value = self.cleaned_data['max_cache_size']
        if value < 1:
            raise ValidationError('Максимальный размер кэша должен быть не менее 1 МБ')
        if value > 1024:
            raise ValidationError('Максимальный размер кэша не должен превышать 1 ГБ')
        return value
    
    def clean_rate_limit_per_minute(self):
        """Валидация лимита запросов в минуту"""
        value = self.cleaned_data['rate_limit_per_minute']
        if value < 1:
            raise ValidationError('Лимит запросов в минуту должен быть не менее 1')
        if value > 1000:
            raise ValidationError('Лимит запросов в минуту не должен превышать 1000')
        return value
    
    def clean_health_check_interval(self):
        """Валидация интервала проверки здоровья"""
        value = self.cleaned_data['health_check_interval']
        if value < 10:
            raise ValidationError('Интервал проверки здоровья должен быть не менее 10 секунд')
        if value > 3600:
            raise ValidationError('Интервал проверки здоровья не должен превышать 1 час')
        return value
    
    def clean_backup_interval_hours(self):
        """Валидация интервала резервного копирования"""
        value = self.cleaned_data['backup_interval_hours']
        if value < 1:
            raise ValidationError('Интервал резервного копирования должен быть не менее 1 часа')
        if value > 168:
            raise ValidationError('Интервал резервного копирования не должен превышать 7 дней')
        return value
    
    def clean_backup_retention_days(self):
        """Валидация срока хранения резервных копий"""
        value = self.cleaned_data['backup_retention_days']
        if value < 1:
            raise ValidationError('Срок хранения резервных копий должен быть не менее 1 дня')
        if value > 365:
            raise ValidationError('Срок хранения резервных копий не должен превышать 365 дней')
        return value
    
    def clean(self):
        """Общая валидация формы"""
        cleaned_data = super().clean()
        
        # Проверяем логические связи между настройками
        enable_cache = cleaned_data.get('enable_cache')
        cache_timeout = cleaned_data.get('cache_timeout')
        max_cache_size = cleaned_data.get('max_cache_size')
        
        if enable_cache and not cache_timeout:
            self.add_error('cache_timeout', 'Необходимо указать таймаут кэша при включенном кэшировании')
        
        if enable_cache and not max_cache_size:
            self.add_error('max_cache_size', 'Необходимо указать максимальный размер кэша при включенном кэшировании')
        
        return cleaned_data


class QuickServerSettingsForm(forms.Form):
    """Быстрая форма для основных настроек сервера"""
    
    server_name = forms.CharField(
        max_length=100,
        label='Название сервера',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'WARA Server'
        })
    )
    
    log_level = forms.ChoiceField(
        choices=ServerSettings._meta.get_field('log_level').choices,
        label='Уровень логирования',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    enable_cache = forms.BooleanField(
        required=False,
        label='Включить кэширование',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    enable_backup = forms.BooleanField(
        required=False,
        label='Автоматическое резервное копирование',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        settings = kwargs.pop('settings', None)
        super().__init__(*args, **kwargs)
        
        if settings:
            self.fields['server_name'].initial = settings.server_name
            self.fields['log_level'].initial = settings.log_level
            self.fields['enable_cache'].initial = settings.enable_cache
            self.fields['enable_backup'].initial = settings.enable_backup
