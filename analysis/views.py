from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, DeleteView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Comparison, AnalysisSettings
from .forms import ComparisonCreateForm, OllamaComparisonForm
from .services import DocumentComparisonService, AnalysisSettingsService
from .ollama_service import OllamaService
from reports.services import AutoReportGeneratorService
import logging
import json

logger = logging.getLogger(__name__)


class ComparisonListView(LoginRequiredMixin, ListView):
    """
    Список сравнений пользователя
    """
    model = Comparison
    template_name = 'analysis/comparison_list.html'
    context_object_name = 'comparisons'
    
    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user).order_by('-created_date')
    
    def get_paginate_by(self, queryset):
        """Получить количество элементов на странице из настроек приложения"""
        from settings.models import ApplicationSettings
        settings = ApplicationSettings.get_settings()
        return settings.items_per_page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем режим просмотра из GET параметров или сессии
        view_mode = self.request.GET.get('view_mode', self.request.session.get('analysis_view_mode', 'card'))
        context['view_mode'] = view_mode
        
        # Сохраняем режим в сессии
        self.request.session['analysis_view_mode'] = view_mode
            
        return context


class ComparisonDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр сравнения
    """
    model = Comparison
    template_name = 'analysis/comparison_detail.html'
    context_object_name = 'comparison'
    
    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comparison = self.get_object()
        
        # Получаем отчеты, связанные с этим сравнением
        reports = comparison.reports.filter(status='ready').order_by('-generated_date')
        context['reports'] = reports
        context['latest_report'] = reports.first() if reports.exists() else None
        
        return context


class ComparisonCreateView(LoginRequiredMixin, CreateView):
    """
    Создание нового сравнения
    """
    model = Comparison
    form_class = ComparisonCreateForm
    template_name = 'analysis/comparison_create.html'
    success_url = reverse_lazy('analysis:list')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Сохраняем сравнение
        response = super().form_valid(form)
        
        # Автоматический запуск анализа
        try:
            # Устанавливаем статус обработки
            form.instance.status = 'processing'
            form.instance.save()
            
            # Выполняем анализ документов
            comparison_service = DocumentComparisonService()
            analysis_result = comparison_service.compare_documents(form.instance)
            
            # Сохраняем результаты
            comparison_service.save_comparison_results(form.instance, analysis_result)
            
            # Обновляем статус и дату завершения
            form.instance.status = 'completed'
            form.instance.completed_date = timezone.now()
            form.instance.save()
            
            # Автоматическая генерация отчетов
            try:
                auto_report_service = AutoReportGeneratorService()
                report_results = auto_report_service.generate_auto_reports(form.instance)
                
                # Подсчитываем успешно созданные отчеты (теперь только один)
                reports_created = 0
                report_format = None
                if report_results.get('pdf_report'):
                    reports_created = 1
                    report_format = 'PDF'
                if report_results.get('docx_report'):
                    reports_created = 1
                    report_format = 'DOCX'
                
                # Подсчитываем изменения для уведомления
                changes_count = len(analysis_result.get('changes', []))
                
                if reports_created > 0:
                    messages.success(self.request, 
                        f'Сравнение успешно создано и проанализировано! '
                        f'Найдено изменений: {changes_count}. '
                        f'Автоматически создан отчет в формате {report_format}.')
                else:
                    messages.success(self.request, 
                        f'Сравнение успешно создано и проанализировано! '
                        f'Найдено изменений: {changes_count}. '
                        f'Ошибка создания отчета - проверьте раздел "Отчеты".')
                
                # Показываем ошибки генерации отчетов, если есть
                for error in report_results.get('errors', []):
                    messages.warning(self.request, f'Ошибка генерации отчета: {error}')
                    
            except Exception as report_error:
                logger.error(f"Ошибка автоматической генерации отчетов для сравнения {form.instance.id}: {report_error}")
                changes_count = len(analysis_result.get('changes', []))
                messages.success(self.request, 
                    f'Сравнение успешно создано и проанализировано! '
                    f'Найдено изменений: {changes_count}. '
                    f'Ошибка автоматической генерации отчетов.')
                
        except Exception as e:
            logger.error(f"Ошибка автоматического анализа сравнения {form.instance.id}: {e}")
            # Устанавливаем статус ошибки
            form.instance.status = 'error'
            form.instance.save()
            
            messages.warning(self.request, 
                f'Сравнение создано, но автоматический анализ не удался. '
                f'Вы можете запустить анализ вручную.')
        
        return response
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class ComparisonRunView(LoginRequiredMixin, DetailView):
    """
    Запуск анализа сравнения
    """
    model = Comparison
    template_name = 'analysis/comparison_run.html'
    
    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        comparison = self.get_object()
        
        if comparison.status == 'pending':
            try:
                # Устанавливаем статус обработки
                comparison.status = 'processing'
                comparison.save()
                
                # Выполняем анализ документов
                comparison_service = DocumentComparisonService()
                analysis_result = comparison_service.compare_documents(comparison)
                
                # Сохраняем результаты
                comparison_service.save_comparison_results(comparison, analysis_result)
                
                messages.success(request, 'Анализ завершен успешно!')
                
            except Exception as e:
                comparison.status = 'error'
                comparison.save()
                logger.error(f"Ошибка при анализе сравнения {comparison.id}: {str(e)}")
                messages.error(request, f'Ошибка при анализе: {str(e)}')
        
        elif comparison.status == 'completed':
            messages.info(request, 'Анализ уже выполнен.')
        elif comparison.status == 'processing':
            messages.warning(request, 'Анализ уже выполняется.')
        elif comparison.status == 'error':
            messages.error(request, 'Произошла ошибка при предыдущем анализе.')
        
        return redirect('analysis:detail', pk=comparison.pk)


class AnalysisSettingsView(LoginRequiredMixin, DetailView):
    """
    Настройки анализа
    """
    model = AnalysisSettings
    template_name = 'analysis/settings.html'
    
    def get_object(self):
        settings, created = AnalysisSettings.objects.get_or_create(
            user=self.request.user
        )
        return settings


class ComparisonDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление сравнения (анализа)
    """
    model = Comparison
    template_name = 'analysis/comparison_confirm_delete.html'
    success_url = reverse_lazy('analysis:list')
    
    def get_queryset(self):
        """Показываем только сравнения текущего пользователя"""
        return Comparison.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        """
        Переопределяем метод delete для добавления сообщения
        """
        comparison = self.get_object()
        comparison_title = comparison.title
        
        # Удаляем связанные отчеты
        reports_count = comparison.reports.count()
        if reports_count > 0:
            comparison.reports.all().delete()
            messages.success(request, 
                f'Анализ "{comparison_title}" и {reports_count} связанных отчетов успешно удалены.')
        else:
            messages.success(request, f'Анализ "{comparison_title}" успешно удален.')
        
        return super().delete(request, *args, **kwargs)


class ComparisonBulkDeleteView(LoginRequiredMixin, View):
    """
    Массовое удаление выбранных анализов
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Удаляет выбранные анализы"""
        try:
            # Получаем данные из JSON запроса
            data = json.loads(request.body)
            comparison_ids = data.get('comparison_ids', [])
            
            if not comparison_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Не выбрано ни одного анализа для удаления'
                })
            
            # Получаем анализы пользователя
            comparisons = Comparison.objects.filter(
                id__in=comparison_ids,
                user=request.user
            )
            
            if not comparisons.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Выбранные анализы не найдены или не принадлежат вам'
                })
            
            # Подсчитываем количество анализов и связанных объектов
            comparisons_count = comparisons.count()
            reports_count = 0
            
            # Подсчитываем связанные отчеты
            for comparison in comparisons:
                reports_count += comparison.reports.count()
            
            # Удаляем анализы (каскадное удаление позаботится о связанных объектах)
            comparisons.delete()
            
            logger.info(f"User {request.user.username} bulk deleted {comparisons_count} comparisons, {reports_count} reports")
            
            return JsonResponse({
                'success': True,
                'message': f'Успешно удалено: {comparisons_count} анализов, {reports_count} отчетов',
                'deleted_count': comparisons_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка в формате данных'
            })
        except Exception as e:
            logger.error(f"Error in bulk delete comparisons by user {request.user.username}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при удалении анализов: {str(e)}'
            })


class OllamaComparisonCreateView(LoginRequiredMixin, View):
    """
    Создание сравнения с помощью нейросети Ollama
    """
    
    def get(self, request):
        """Показывает форму для создания анализа"""
        form = OllamaComparisonForm(user=request.user)
        
        # Проверяем доступность Ollama
        ollama_service = OllamaService()
        ollama_available = ollama_service.is_available()
        available_models = ollama_service.get_available_models() if ollama_available else []
        
        # Создаем читаемые названия моделей
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
        
        readable_models = []
        for model in available_models:
            display_name = model_display_names.get(model, model)
            readable_models.append(display_name)
        
        context = {
            'form': form,
            'ollama_available': ollama_available,
            'available_models': readable_models,
        }
        
        return render(request, 'analysis/ollama_comparison_create.html', context)
    
    def post(self, request):
        """Обрабатывает создание анализа"""
        form = OllamaComparisonForm(user=request.user, data=request.POST)
        
        if form.is_valid():
            try:
                base_document = form.cleaned_data['base_document']
                compared_document = form.cleaned_data['compared_document']
                analysis_type = form.cleaned_data['analysis_type']
                model = form.cleaned_data['model']
                title = form.cleaned_data['title']
                
                # Создаем сервис Ollama с выбранной моделью
                ollama_service = OllamaService(model=model)
                
                # Проверяем доступность сервиса
                if not ollama_service.is_available():
                    messages.error(request, 'Сервис Ollama недоступен. Убедитесь, что Ollama запущен на localhost:11434')
                    return render(request, 'analysis/ollama_comparison_create.html', {'form': form})
                
                # Получаем содержимое документов
                base_content = base_document.get_content_text()
                compared_content = compared_document.get_content_text()
                
                if not base_content or not compared_content:
                    messages.error(request, 'Один или оба документа не содержат текста для анализа')
                    return render(request, 'analysis/ollama_comparison_create.html', {'form': form})
                
                # Выполняем анализ в зависимости от типа
                if analysis_type == 'comparison':
                    result = ollama_service.compare_documents(
                        base_content, compared_content,
                        base_document.title, compared_document.title
                    )
                elif analysis_type == 'sentiment':
                    # Анализируем тональность обоих документов
                    base_sentiment = ollama_service.analyze_document_sentiment(base_content)
                    compared_sentiment = ollama_service.analyze_document_sentiment(compared_content)
                    
                    result = {
                        "success": True,
                        "comparison_result": {
                            "summary": "Анализ тональности документов",
                            "base_document_sentiment": base_sentiment.get("sentiment_result", {}),
                            "compared_document_sentiment": compared_sentiment.get("sentiment_result", {}),
                            "similarities": [],
                            "differences": [],
                            "recommendations": [],
                            "overall_assessment": "Сравнение тональности документов"
                        }
                    }
                elif analysis_type == 'key_points':
                    # Извлекаем ключевые моменты из обоих документов
                    base_key_points = ollama_service.extract_key_points(base_content)
                    compared_key_points = ollama_service.extract_key_points(compared_content)
                    
                    result = {
                        "success": True,
                        "comparison_result": {
                            "summary": "Извлечение ключевых моментов из документов",
                            "base_document_key_points": base_key_points.get("key_points_result", {}),
                            "compared_document_key_points": compared_key_points.get("key_points_result", {}),
                            "similarities": [],
                            "differences": [],
                            "recommendations": [],
                            "overall_assessment": "Сравнение ключевых моментов документов"
                        }
                    }
                else:
                    messages.error(request, 'Неизвестный тип анализа')
                    return render(request, 'analysis/ollama_comparison_create.html', {'form': form})
                
                if result["success"]:
                    # Создаем запись о сравнении
                    comparison = Comparison.objects.create(
                        user=request.user,
                        title=title,
                        base_document=base_document,
                        compared_document=compared_document,
                        status='completed',
                        analysis_type='ollama',
                        analysis_method=f'ollama_{model}',
                        analysis_result=result["comparison_result"]
                    )
                    
                    # Автоматически создаем отчет
                    try:
                        from reports.services import OllamaReportGeneratorService
                        from settings.models import ApplicationSettings
                        
                        # Получаем формат отчета из настроек
                        settings = ApplicationSettings.get_settings()
                        report_format = settings.default_report_format
                        
                        # Создаем сервис генерации отчетов
                        report_service = OllamaReportGeneratorService()
                        report = report_service.save_ollama_report(comparison, report_format)
                        
                        messages.success(request, 
                            f'Анализ с помощью нейросети {model} успешно выполнен! '
                            f'Автоматически создан отчет в формате {report_format.upper()}.')
                        
                    except Exception as report_error:
                        logger.error(f"Ошибка при создании отчета анализа нейросетью: {report_error}")
                        messages.success(request, f'Анализ с помощью нейросети {model} успешно выполнен! ')
                        messages.warning(request, f'Ошибка создания отчета: {report_error}')
                    
                    return redirect('analysis:ollama_detail', pk=comparison.pk)
                else:
                    error_msg = result.get("error", "Неизвестная ошибка при анализе")
                    messages.error(request, f'Ошибка при анализе: {error_msg}')
                    logger.error(f"Ollama analysis error: {error_msg}")
                
            except Exception as e:
                error_msg = f'Ошибка при выполнении анализа: {str(e)}'
                messages.error(request, error_msg)
                logger.error(f"Ollama comparison error: {error_msg}")
        
        # Проверяем доступность Ollama для контекста
        ollama_service = OllamaService()
        ollama_available = ollama_service.is_available()
        available_models = ollama_service.get_available_models() if ollama_available else []
        
        context = {
            'form': form,
            'ollama_available': ollama_available,
            'available_models': available_models,
        }
        
        return render(request, 'analysis/ollama_comparison_create.html', context)


class OllamaComparisonDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр результата анализа с помощью Ollama
    """
    model = Comparison
    template_name = 'analysis/ollama_comparison_detail.html'
    context_object_name = 'comparison'
    
    def get_queryset(self):
        return Comparison.objects.filter(user=self.request.user, analysis_type='ollama')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        comparison = self.get_object()
        
        # Добавляем информацию о модели
        context['model_info'] = {
            'method': comparison.analysis_method,
            'type': comparison.analysis_type,
        }
        
        # Добавляем информацию об отчетах
        reports = comparison.reports.filter(status='ready').order_by('-generated_date')
        context['reports'] = reports
        context['latest_report'] = reports.first()
        
        return context


class OllamaStatusView(LoginRequiredMixin, View):
    """
    Проверка статуса Ollama сервиса
    """
    
    def get(self, request):
        """Возвращает статус Ollama сервиса"""
        ollama_service = OllamaService()
        
        status = {
            'available': ollama_service.is_available(),
            'models': []
        }
        
        if status['available']:
            status['models'] = ollama_service.get_available_models()
        
        return JsonResponse(status)