"""
Формы для работы с отчетами
"""
from django import forms
from .models import Report, ReportTemplate

class ReportEmailForm(forms.Form):
    """
    Форма для отправки отчета по email
    """
    recipient_email = forms.EmailField(
        label='Email получателя',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@company.com'
        }),
        help_text='Введите email адрес получателя отчета'
    )
    
    message = forms.CharField(
        label='Дополнительное сообщение',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Введите дополнительное сообщение для получателя...'
        }),
        required=False,
        help_text='Необязательное сообщение, которое будет включено в email'
    )
    
    def clean_recipient_email(self):
        email = self.cleaned_data['recipient_email']
        # Здесь можно добавить дополнительную валидацию
        return email.lower()


class ReportTemplateForm(forms.ModelForm):
    """
    Форма для создания и редактирования шаблонов отчетов
    """
    
    class Meta:
        model = ReportTemplate
        fields = ['name', 'template_content', 'is_default']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название шаблона'
            }),
            'template_content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 15,
                'placeholder': 'Содержимое шаблона в HTML/Markdown формате'
            }),
            'is_default': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Название шаблона',
            'template_content': 'Содержимое шаблона',
            'is_default': 'Шаблон по умолчанию'
        }
    
    def clean_name(self):
        name = self.cleaned_data['name']
        if ReportTemplate.objects.filter(name=name).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('Шаблон с таким названием уже существует')
        return name
    
    def clean_is_default(self):
        is_default = self.cleaned_data['is_default']
        if is_default:
            # Если устанавливаем как шаблон по умолчанию, снимаем флаг с других
            ReportTemplate.objects.filter(is_default=True).update(is_default=False)
        return is_default


class ReportGenerateForm(forms.Form):
    """
    Форма для генерации отчета
    """
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('docx', 'Word Document'),
        ('xlsx', 'Excel Spreadsheet'),
    ]
    
    TEMPLATE_CHOICES = [
        ('default', 'Стандартный шаблон'),
        ('detailed', 'Детальный шаблон'),
        ('summary', 'Краткий шаблон'),
    ]
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label='Формат отчета',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем формат по умолчанию из настроек приложения
        from settings.models import ApplicationSettings
        try:
            settings = ApplicationSettings.get_settings()
            self.fields['format'].initial = settings.default_report_format
        except:
            self.fields['format'].initial = 'pdf'
    
    template = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        label='Шаблон отчета',
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='default'
    )
    
    include_charts = forms.BooleanField(
        label='Включить диаграммы',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        initial=True
    )
    
    include_metadata = forms.BooleanField(
        label='Включить метаданные документов',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        initial=True
    )
    
    email_after_generation = forms.BooleanField(
        label='Отправить по email после генерации',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        required=False,
        initial=False
    )
    
    email_recipient = forms.EmailField(
        label='Email для отправки',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'example@company.com'
        }),
        required=False
    )
    
    def clean_email_recipient(self):
        email_recipient = self.cleaned_data.get('email_recipient')
        email_after_generation = self.cleaned_data.get('email_after_generation', False)
        
        if email_after_generation and not email_recipient:
            raise forms.ValidationError('Укажите email получателя для отправки отчета')
        
        return email_recipient


class ReportFilterForm(forms.Form):
    """
    Форма для фильтрации отчетов
    """
    STATUS_CHOICES = [
        ('', 'Все статусы'),
        ('generated', 'Сгенерирован'),
        ('sent', 'Отправлен'),
        ('error', 'Ошибка'),
    ]
    
    FORMAT_CHOICES = [
        ('', 'Все форматы'),
        ('pdf', 'PDF'),
        ('docx', 'Word'),
        ('xlsx', 'Excel'),
    ]
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label='Статус',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label='Формат',
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=False
    )
    
    date_from = forms.DateField(
        label='Дата с',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    date_to = forms.DateField(
        label='Дата по',
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        required=False
    )
    
    search = forms.CharField(
        label='Поиск',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Поиск по названию отчета...'
        }),
        required=False
    )
