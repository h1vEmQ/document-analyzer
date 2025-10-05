from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, DeleteView, View
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from .models import Document
from .forms import DocumentUploadForm, DocumentVersionUploadForm, DocumentRenameForm
from .services import DocumentParserService, DocumentValidationService
import logging
import json

logger = logging.getLogger(__name__)


class DocumentListView(LoginRequiredMixin, ListView):
    """
    Список документов пользователя
    """
    model = Document
    template_name = 'documents/document_list.html'
    context_object_name = 'documents'

    def get_queryset(self):
        # Показываем только корневые документы (без версий) и документы без родителя
        return Document.objects.filter(
            user=self.request.user,
            parent_document__isnull=True  # Только документы без родителя (корневые)
        ).order_by('-upload_date')
    
    def get_paginate_by(self, queryset):
        """Получить количество элементов на странице из настроек приложения"""
        from settings.models import ApplicationSettings
        settings = ApplicationSettings.get_settings()
        return settings.items_per_page
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем режим просмотра из GET параметров или сессии
        view_mode = self.request.GET.get('view_mode', self.request.session.get('document_view_mode', 'card'))
        context['view_mode'] = view_mode
        
        # Сохраняем режим в сессии
        self.request.session['document_view_mode'] = view_mode
        
        # Устанавливаем соответствующий шаблон
        if view_mode == 'table':
            context['template_name'] = 'documents/document_list_table.html'
        else:
            context['template_name'] = 'documents/document_list_card.html'
            
        return context


class DocumentDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр документа
    """
    model = Document
    template_name = 'documents/document_detail.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)


class DocumentUploadView(LoginRequiredMixin, CreateView):
    """
    Загрузка нового документа или создание новой версии существующего
    """
    model = Document
    form_class = DocumentUploadForm
    template_name = 'documents/document_upload.html'
    success_url = reverse_lazy('documents:list')
    
    def get_form_kwargs(self):
        """Передаем пользователя в форму"""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        
        # Проверяем, создается ли новая версия существующего документа
        existing_document = form.cleaned_data.get('existing_document')
        version_notes = form.cleaned_data.get('version_notes', '')
        
        if existing_document:
            # Создаем новую версию существующего документа
            form.instance.parent_document = existing_document
            form.instance.version = existing_document.get_next_version()
            form.instance.is_latest_version = True
            
            # Обновляем предыдущую версию
            existing_document.is_latest_version = False
            existing_document.save()
            
            # Добавляем заметки к версии
            if version_notes:
                form.instance.version_notes = version_notes
        
        # Валидация файла
        validation_service = DocumentValidationService()
        validation_result = validation_service.validate_upload(form.instance.file)
        
        if not validation_result['is_valid']:
            for error in validation_result['errors']:
                form.add_error('file', error)
            return self.form_invalid(form)
        
        # Показываем предупреждения
        for warning in validation_result['warnings']:
            messages.warning(self.request, warning)
        
        # Сохраняем документ
        response = super().form_valid(form)
        
        # Автоматическая обработка файла
        try:
            # Устанавливаем статус обработки
            form.instance.status = 'processing'
            form.instance.save()
            
            # Парсинг документа
            parser_service = DocumentParserService()
            parse_result = parser_service.parse_document(form.instance)
            
            if parse_result['success']:
                content_data = parse_result['content_data']
                
                # Сохранение результатов
                parser_service.save_parsed_content(form.instance, content_data)
                
                # Обновляем статус и дату обработки
                form.instance.status = 'processed'
                form.instance.processed_date = timezone.now()
                form.instance.save()
                
                # Если парсинг прошел успешно, content_data содержит данные
                if content_data and 'sections' in content_data:
                    sections_count = len(content_data['sections'])
                    tables_count = len(content_data['tables'])
                    
                    if existing_document:
                        messages.success(self.request, 
                            f'Новая версия документа успешно создана и обработана! '
                            f'Версия: {form.instance.version} '
                            f'(найдено разделов: {sections_count}, таблиц: {tables_count})')
                    else:
                        messages.success(self.request, 
                            f'Документ успешно загружен и обработан! '
                            f'Найдено разделов: {sections_count}, '
                            f'таблиц: {tables_count}')
                else:
                    messages.warning(self.request, 
                        'Документ загружен, но обработка завершилась с ошибками.')
            else:
                # Парсинг не удался
                form.instance.status = 'error'
                form.instance.save()
                messages.error(self.request, 
                    f'Ошибка при обработке документа: {parse_result.get("error", "Неизвестная ошибка")}')
                
        except Exception as e:
            logger.error(f"Ошибка автоматической обработки документа {form.instance.id}: {e}")
            # Устанавливаем статус ошибки
            form.instance.status = 'error'
            form.instance.save()
            
            messages.warning(self.request, 
                f'Документ загружен, но автоматическая обработка не удалась. '
                f'Вы можете запустить обработку вручную.')
        
        return response


class DocumentParseView(LoginRequiredMixin, DetailView):
    """
    Запуск парсинга документа
    """
    model = Document
    template_name = 'documents/document_parse.html'
    
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        document = self.get_object()
        
        if document.status == 'uploaded':
            try:
                # Устанавливаем статус обработки
                document.status = 'processing'
                document.save()
                
                # Парсинг документа
                parser_service = DocumentParserService()
                content_data = parser_service.parse_document(document)
                
                # Сохранение результатов
                parser_service.save_parsed_content(document, content_data)
                
                # Обновляем дату обработки
                document.processed_date = timezone.now()
                document.save()
                
                messages.success(request, 'Документ успешно обработан!')
                
            except ValidationError as e:
                document.status = 'error'
                document.save()
                messages.error(request, f'Ошибка при обработке документа: {str(e)}')
                
            except Exception as e:
                document.status = 'error'
                document.save()
                logger.error(f"Неожиданная ошибка при парсинге документа {document.id}: {str(e)}")
                messages.error(request, 'Произошла неожиданная ошибка при обработке документа.')
        
        elif document.status == 'processed':
            messages.info(request, 'Документ уже обработан.')
        elif document.status == 'processing':
            messages.warning(request, 'Документ уже обрабатывается.')
        elif document.status == 'error':
            messages.error(request, 'Документ содержит ошибки. Попробуйте загрузить другой файл.')
        
        return redirect('documents:detail', pk=document.pk)


class DocumentDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление документа
    """
    model = Document
    template_name = 'documents/document_confirm_delete.html'
    success_url = reverse_lazy('documents:list')
    
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Документ успешно удален!')
        return super().delete(request, *args, **kwargs)


class DocumentVersionUploadView(LoginRequiredMixin, View):
    """
    Загрузка новой версии документа
    """
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)
        form = DocumentVersionUploadForm()
        return render(request, 'documents/document_version_upload.html', {
            'document': document,
            'form': form
        })
    
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)
        form = DocumentVersionUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Валидация файла
                validation_service = DocumentValidationService()
                validation_result = validation_service.validate_upload(form.cleaned_data['file'])
                
                if not validation_result['is_valid']:
                    for error in validation_result['errors']:
                        form.add_error('file', error)
                    return render(request, 'documents/document_version_upload.html', {
                        'document': document,
                        'form': form
                    })
                
                # Показываем предупреждения
                for warning in validation_result['warnings']:
                    messages.warning(request, warning)
                
                # Создаем новую версию
                new_document = document.create_new_version(
                    form.cleaned_data['file'],
                    form.cleaned_data['version_notes']
                )
                
                # Автоматическая обработка новой версии
                try:
                    # Устанавливаем статус обработки
                    new_document.status = 'processing'
                    new_document.save()
                    
                    # Парсинг документа
                    parser_service = DocumentParserService()
                    content_data = parser_service.parse_document(new_document)
                    
                    # Сохранение результатов
                    parser_service.save_parsed_content(new_document, content_data)
                    
                    # Обновляем статус и дату обработки
                    new_document.status = 'processed'
                    new_document.processed_date = timezone.now()
                    new_document.save()
                    
                    # Уведомление об успехе
                    version_count = new_document.get_version_count()
                    sections_count = len(content_data.get('sections', []))
                    tables_count = len(content_data.get('tables', []))
                    
                    messages.success(request, 
                        f'Новая версия {new_document.version} успешно загружена и обработана! '
                        f'Всего версий: {version_count}. '
                        f'Найдено разделов: {sections_count}, таблиц: {tables_count}')
                        
                except Exception as e:
                    logger.error(f"Ошибка автоматической обработки новой версии {new_document.id}: {e}")
                    new_document.status = 'error'
                    new_document.save()
                    
                    messages.warning(request, 
                        f'Новая версия загружена, но автоматическая обработка не удалась. '
                        f'Вы можете запустить обработку вручную.')
                
                return redirect('documents:detail', pk=new_document.pk)
                
            except Exception as e:
                logger.error(f"Ошибка создания новой версии документа {document.id}: {e}")
                messages.error(request, f'Ошибка при создании новой версии: {str(e)}')
        
        return render(request, 'documents/document_version_upload.html', {
            'document': document,
            'form': form
        })


class DocumentVersionHistoryView(LoginRequiredMixin, DetailView):
    """
    История версий документа
    """
    model = Document
    template_name = 'documents/document_version_history.html'
    context_object_name = 'document'
    
    def get_queryset(self):
        return Document.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        document = self.get_object()
        
        # Получаем корневой документ и его версии
        root_document = document.get_root_document()
        versions = root_document.get_version_history()
        
        context['root_document'] = root_document
        context['versions'] = versions
        context['version_count'] = versions.count()
        context['latest_version'] = root_document.get_latest_version()
        
        return context


class DocumentRenameView(LoginRequiredMixin, View):
    """
    Переименование документа
    """
    def get(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)
        form = DocumentRenameForm(instance=document)
        return render(request, 'documents/document_rename.html', {
            'document': document,
            'form': form
        })
    
    def post(self, request, pk):
        document = get_object_or_404(Document, pk=pk, user=request.user)
        form = DocumentRenameForm(request.POST, instance=document)
        
        if form.is_valid():
            old_title = document.title
            form.save()
            new_title = document.title
            
            messages.success(request, 
                f'Документ успешно переименован: "{old_title}" → "{new_title}"')
            
            return redirect('documents:detail', pk=document.pk)
        
        return render(request, 'documents/document_rename.html', {
            'document': document,
            'form': form
        })


class DocumentVersionDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление версии документа
    """
    model = Document
    template_name = 'documents/document_version_confirm_delete.html'
    
    def get_queryset(self):
        """Показываем только документы текущего пользователя"""
        return Document.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        """Перенаправляем на детальный просмотр документа"""
        document = self.get_object()
        root_document = document.get_root_document()
        return reverse_lazy('documents:detail', kwargs={'pk': root_document.pk})
    
    def delete(self, request, *args, **kwargs):
        """
        Переопределяем метод delete для обработки версий и физических файлов
        """
        document = self.get_object()
        document_title = document.title
        document_version = document.version
        is_latest_version = document.is_latest_version
        is_root_document = document.parent_document is None
        
        # Проверяем, можно ли удалить этот документ
        if is_root_document:
            # Если это корневой документ, проверяем, есть ли другие версии
            version_count = document.get_version_count()
            if version_count > 1:
                messages.error(request, 
                    'Нельзя удалить корневой документ, если есть другие версии. '
                    'Сначала удалите все версии.')
                return redirect('documents:detail', pk=document.pk)
        
        # Удаляем физический файл, если он существует
        if document.file and document.file.path:
            try:
                import os
                if os.path.exists(document.file.path):
                    os.remove(document.file.path)
                    logger.info(f"Deleted physical file: {document.file.path}")
            except OSError as e:
                logger.error(f"Error deleting file {document.file.path}: {str(e)}")
        
        # Обрабатываем версии
        version_count_before = document.get_version_count()
        root_document = document.get_root_document()
        
        # Выполняем удаление
        super().delete(request, *args, **kwargs)
        
        # После удаления обрабатываем версии
        if is_latest_version and version_count_before > 1:
            # Если это была последняя версия, делаем предыдущую последней
            remaining_versions = root_document.get_version_history().order_by('-upload_date')
            if remaining_versions.exists():
                new_latest = remaining_versions.first()
                new_latest.is_latest_version = True
                new_latest.save()
                logger.info(f"Made version {new_latest.version} the latest version")
                messages.success(request, 
                    f'Версия {document_version} документа "{document_title}" удалена. '
                    f'Последней версией стала v{new_latest.version}.')
            else:
                messages.success(request, 
                    f'Версия {document_version} документа "{document_title}" удалена.')
        else:
            messages.success(request, 
                f'Версия {document_version} документа "{document_title}" удалена.')
        
        return redirect(self.get_success_url())


class DocumentBulkDeleteView(LoginRequiredMixin, View):
    """
    Массовое удаление выбранных документов
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Удаляет выбранные документы"""
        try:
            # Получаем данные из JSON запроса
            data = json.loads(request.body)
            document_ids = data.get('document_ids', [])
            
            if not document_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Не выбрано ни одного документа для удаления'
                })
            
            # Получаем документы пользователя
            documents = Document.objects.filter(
                id__in=document_ids,
                user=request.user
            )
            
            if not documents.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Выбранные документы не найдены или не принадлежат вам'
                })
            
            # Подсчитываем количество документов и связанных объектов
            documents_count = documents.count()
            comparisons_count = 0
            reports_count = 0
            
            # Подсчитываем связанные объекты
            for document in documents:
                # Подсчитываем сравнения, где документ является базовым или сравниваемым
                base_comparisons = document.base_comparisons.all()
                compared_comparisons = document.compared_comparisons.all()
                comparisons_count += base_comparisons.count() + compared_comparisons.count()
                
                # Подсчитываем отчеты через сравнения
                for comparison in base_comparisons:
                    reports_count += comparison.reports.count()
                for comparison in compared_comparisons:
                    reports_count += comparison.reports.count()
            
            # Удаляем документы (каскадное удаление позаботится о связанных объектах)
            documents.delete()
            
            logger.info(f"User {request.user.username} bulk deleted {documents_count} documents, {comparisons_count} comparisons, {reports_count} reports")
            
            return JsonResponse({
                'success': True,
                'message': f'Успешно удалено: {documents_count} документов, {comparisons_count} сравнений, {reports_count} отчетов',
                'deleted_count': documents_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка в формате данных'
            })
        except Exception as e:
            logger.error(f"Error in bulk delete by user {request.user.username}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при удалении документов: {str(e)}'
            })