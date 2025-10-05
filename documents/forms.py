from django import forms
from .models import Document


class DocumentRenameForm(forms.ModelForm):
    """
    Форма для переименования документа
    """
    class Meta:
        model = Document
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите новое название документа'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Название документа'
        self.fields['title'].required = True


class DocumentUploadForm(forms.ModelForm):
    """
    Форма для загрузки документа
    """
    # Добавляем поле для выбора существующего документа
    existing_document = forms.ModelChoiceField(
        queryset=Document.objects.none(),
        required=False,
        empty_label="Создать новый документ",
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'id_existing_document'
        }),
        label="Существующий документ"
    )
    
    # Поле для заметок к версии
    version_notes = forms.CharField(
        label='Заметки к версии',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Опишите изменения в новой версии (опционально)',
            'id': 'id_version_notes',
            'style': 'display: none;'
        })
    )
    
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название документа',
                'id': 'id_title'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx',
                'id': 'id_file'
            })
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.fields['title'].label = 'Название документа'
        self.fields['title'].required = False
        self.fields['file'].label = 'Файл документа (.docx)'
        
        # Настраиваем queryset для существующих документов
        if user:
            # Показываем только корневые документы пользователя (без версий)
            self.fields['existing_document'].queryset = Document.objects.filter(
                user=user,
                parent_document__isnull=True
            ).order_by('-upload_date')
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10 МБ')
            
            # Проверяем расширение
            if not file.name.lower().endswith('.docx'):
                raise forms.ValidationError('Файл должен иметь расширение .docx')
            
            # Автоматически заполняем название документа, если оно пустое
            if not self.cleaned_data.get('title'):
                # Убираем расширение из имени файла для названия
                title = file.name.rsplit('.', 1)[0]
                self.cleaned_data['title'] = title
        
        return file
    
    def clean(self):
        cleaned_data = super().clean()
        existing_document = cleaned_data.get('existing_document')
        title = cleaned_data.get('title')
        
        # Если выбран существующий документ, название не обязательно
        if existing_document:
            # Автоматически заполняем название из существующего документа
            if not title:
                cleaned_data['title'] = existing_document.title
        else:
            # Для нового документа название обязательно
            if not title:
                raise forms.ValidationError('Название документа обязательно для новых документов')
        
        return cleaned_data


class DocumentVersionUploadForm(forms.Form):
    """
    Форма для загрузки новой версии документа
    """
    file = forms.FileField(
        label='Новый файл документа (.docx)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.docx'
        })
    )
    
    version_notes = forms.CharField(
        label='Заметки к версии',
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Опишите изменения в новой версии (опционально)'
        })
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверяем размер файла (10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('Размер файла не должен превышать 10 МБ')
            
            # Проверяем расширение
            if not file.name.lower().endswith('.docx'):
                raise forms.ValidationError('Файл должен иметь расширение .docx')
        
        return file
