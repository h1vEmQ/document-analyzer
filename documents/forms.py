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
    class Meta:
        model = Document
        fields = ['title', 'file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название документа'
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.docx'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Название документа'
        self.fields['title'].required = False
        self.fields['file'].label = 'Файл документа (.docx)'
    
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
