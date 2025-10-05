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
        ('deepseek-r1:7b', 'DeepSeek R1 7B'),
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
        
        # Получаем только установленные модели
        available_models = self.get_available_models()
        if available_models:
            self.fields['model'].choices = available_models
            # Устанавливаем первую доступную модель как значение по умолчанию
            self.fields['model'].initial = available_models[0][0]
        else:
            # Если нет доступных моделей, скрываем поле
            self.fields['model'].choices = [('', 'Модели не установлены')]
            self.fields['model'].widget.attrs['disabled'] = True
    
    def get_available_models(self):
        """Получает список доступных моделей из Ollama"""
        try:
            from .ollama_service import OllamaService
            
            # Создаем временный сервис для проверки доступности
            ollama_service = OllamaService()
            
            if not ollama_service.is_available():
                return []
            
            # Получаем список установленных моделей
            installed_models = ollama_service.get_available_models()
            
            if not installed_models:
                return []
            
            # Создаем список выбора из установленных моделей
            available_choices = []
            
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
            
            for model in installed_models:
                # Используем читаемое название если есть, иначе техническое
                display_name = model_display_names.get(model, model)
                available_choices.append((model, display_name))
            
            return available_choices
            
        except Exception as e:
            # В случае ошибки возвращаем пустой список
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Ошибка получения доступных моделей: {e}")
            return []
    
    def clean(self):
        cleaned_data = super().clean()
        base_document = cleaned_data.get('base_document')
        compared_document = cleaned_data.get('compared_document')
        analysis_type = cleaned_data.get('analysis_type')
        
        if base_document and compared_document:
            if base_document == compared_document:
                raise forms.ValidationError('Базовый и сравниваемый документы не могут быть одинаковыми')
        
        # Проверяем доступность выбранной модели
        selected_model = cleaned_data.get('model')
        if selected_model:
            available_models = self.get_available_models()
            available_model_names = [choice[0] for choice in available_models]
            
            if selected_model not in available_model_names:
                raise forms.ValidationError('Выбранная модель не установлена или недоступна')
        
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
