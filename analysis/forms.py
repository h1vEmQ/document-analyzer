from django import forms
from .models import Comparison
from documents.models import Document


class ComparisonCreateForm(forms.ModelForm):
    """
    Форма для создания сравнения
    """
    class Meta:
        model = Comparison
        fields = ['title', 'base_document', 'compared_document']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите название сравнения'
            }),
            'base_document': forms.Select(attrs={
                'class': 'form-control'
            }),
            'compared_document': forms.Select(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].label = 'Название сравнения'
        self.fields['title'].required = False
        self.fields['base_document'].label = 'Базовый документ'
        self.fields['compared_document'].label = 'Сравниваемый документ'
        
        # Фильтруем документы только текущего пользователя
        processed_docs = Document.objects.filter(
            user=user,
            status='processed'
        ).order_by('-upload_date')
        
        self.fields['base_document'].queryset = processed_docs
        self.fields['compared_document'].queryset = processed_docs
    
    def clean(self):
        cleaned_data = super().clean()
        base_document = cleaned_data.get('base_document')
        compared_document = cleaned_data.get('compared_document')
        
        if base_document and compared_document:
            if base_document == compared_document:
                raise forms.ValidationError('Базовый и сравниваемый документы не могут быть одинаковыми')
            
            # Автоматически заполняем название сравнения, если оно пустое
            if not cleaned_data.get('title'):
                # Создаем название из имен документов с версиями
                base_name = base_document.title
                compared_name = compared_document.title
                
                # Добавляем номера версий
                base_version = base_document.version
                compared_version = compared_document.version
                
                # Проверяем, являются ли документы версиями одного документа
                is_version_comparison = (
                    base_document.parent_document == compared_document.parent_document and
                    base_document.parent_document is not None
                )
                
                if is_version_comparison:
                    # Для сравнения версий используем более компактное название
                    root_doc = base_document.parent_document
                    # Ограничиваем длину названия корневого документа
                    root_name = root_doc.title
                    if len(root_name) > 40:
                        root_name = root_name[:37] + "..."
                    title = f"{root_name} (v{base_version} → v{compared_version})"
                else:
                    # Для сравнения разных документов добавляем версии к названиям
                    base_with_version = f"{base_name} (v{base_version})"
                    compared_with_version = f"{compared_name} (v{compared_version})"
                    
                    # Ограничиваем длину названий для читаемости
                    if len(base_with_version) > 35:
                        base_with_version = base_name[:25] + f" (v{base_version})"
                    if len(compared_with_version) > 35:
                        compared_with_version = compared_name[:25] + f" (v{compared_version})"
                    
                    title = f"{base_with_version} vs {compared_with_version}"
                
                cleaned_data['title'] = title
        
        return cleaned_data


class OllamaComparisonForm(forms.Form):
    """
    Форма для сравнения документов с помощью нейросети
    """
    
    ANALYSIS_TYPE_CHOICES = [
        ('comparison', 'Сравнение документов'),
        ('sentiment', 'Анализ тональности'),
        ('key_points', 'Извлечение ключевых моментов'),
    ]
    
    MODEL_CHOICES = [
        ('llama3', 'Llama 3'),
        ('llama3.1', 'Llama 3.1'),
        ('mistral', 'Mistral'),
        ('codellama', 'Code Llama'),
    ]
    
    base_document = forms.ModelChoiceField(
        queryset=Document.objects.none(),
        label='Базовый документ',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    compared_document = forms.ModelChoiceField(
        queryset=Document.objects.none(),
        label='Сравниваемый документ',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    analysis_type = forms.ChoiceField(
        choices=ANALYSIS_TYPE_CHOICES,
        label='Тип анализа',
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='comparison'
    )
    
    model = forms.ChoiceField(
        choices=MODEL_CHOICES,
        label='Модель нейросети',
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial='llama3'
    )
    
    title = forms.CharField(
        max_length=200,
        label='Название анализа',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите название анализа (необязательно)'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Фильтруем документы только текущего пользователя
        processed_docs = Document.objects.filter(
            user=user,
            status='processed'
        ).order_by('-upload_date')
        
        self.fields['base_document'].queryset = processed_docs
        self.fields['compared_document'].queryset = processed_docs
    
    def clean(self):
        cleaned_data = super().clean()
        base_document = cleaned_data.get('base_document')
        compared_document = cleaned_data.get('compared_document')
        analysis_type = cleaned_data.get('analysis_type')
        
        if base_document and compared_document:
            if base_document == compared_document:
                raise forms.ValidationError('Базовый и сравниваемый документы не могут быть одинаковыми')
        
        # Автоматически заполняем название анализа, если оно пустое
        if not cleaned_data.get('title') and base_document and compared_document:
            analysis_type_names = {
                'comparison': 'Сравнение',
                'sentiment': 'Анализ тональности',
                'key_points': 'Ключевые моменты'
            }
            
            analysis_name = analysis_type_names.get(analysis_type, 'Анализ')
            title = f"{analysis_name}: {base_document.title} vs {compared_document.title}"
            
            # Ограничиваем длину названия
            if len(title) > 200:
                base_name = base_document.title[:50]
                compared_name = compared_document.title[:50]
                title = f"{analysis_name}: {base_name} vs {compared_name}"
            
            cleaned_data['title'] = title
        
        return cleaned_data
