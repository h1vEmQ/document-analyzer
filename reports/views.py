from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, View, DeleteView
from django.http import HttpResponse, Http404, JsonResponse
from django.core.files.base import ContentFile
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import os
import json
from .models import Report, ReportTemplate
from .services import PDFReportGeneratorService, EmailReportService, ReportTemplateService
import logging

logger = logging.getLogger(__name__)


class ReportListView(LoginRequiredMixin, ListView):
    """
    Список отчетов пользователя
    """
    model = Report
    template_name = 'reports/report_list.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        # Показываем только корневые отчеты (не версии)
        return Report.objects.filter(user=self.request.user, parent_report__isnull=True).order_by('-generated_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Получаем режим просмотра из GET параметров или сессии
        view_mode = self.request.GET.get('view_mode', self.request.session.get('reports_view_mode', 'card'))
        context['view_mode'] = view_mode
        
        # Сохраняем режим в сессии
        self.request.session['reports_view_mode'] = view_mode
            
        return context


class ReportDetailView(LoginRequiredMixin, DetailView):
    """
    Детальный просмотр отчета
    """
    model = Report
    template_name = 'reports/report_detail.html'
    context_object_name = 'report'
    
    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        report = self.get_object()
        
        # Получаем корневой отчет и все его версии
        root_report = report.get_root_report()
        all_versions = root_report.get_version_history()
        
        # Статистика версий
        total_versions = all_versions.count()
        latest_version = root_report.get_latest_version()
        
        context.update({
            'root_report': root_report,
            'all_versions': all_versions,
            'total_versions': total_versions,
            'latest_version': latest_version,
            'current_report': report,
            'is_current_latest': report.is_latest_version,
            'is_root_report': report.parent_report is None,
        })
        
        return context


class ReportDownloadView(LoginRequiredMixin, DetailView):
    """
    Скачивание отчета
    """
    model = Report
    
    def get_queryset(self):
        return Report.objects.filter(user=self.request.user)
    
    def get(self, request, *args, **kwargs):
        report = self.get_object()
        
        if not report.file:
            raise Http404("Файл отчета не найден")
        
        if not os.path.exists(report.file.path):
            raise Http404("Файл отчета недоступен")
        
        # Отправляем файл для скачивания
        response = HttpResponse(
            report.file.read(),
            content_type='application/octet-stream'
        )
        response['Content-Disposition'] = f'attachment; filename="{report.title}.{report.format}"'
        
        return response


class ReportGenerateView(LoginRequiredMixin, View):
    """
    Генерация отчета на основе сравнения
    """
    
    def get(self, request, comparison_id):
        from analysis.models import Comparison
        from settings.models import ApplicationSettings
        
        comparison = get_object_or_404(Comparison, id=comparison_id, user=request.user)
        
        if comparison.status != 'completed':
            messages.error(request, 'Сравнение должно быть завершено перед генерацией отчета')
            return redirect('analysis:detail', pk=comparison.pk)
        
        try:
            # Получаем формат отчета из настроек приложения
            settings = ApplicationSettings.get_settings()
            report_format = settings.default_report_format
            
            # Генерируем отчет в выбранном формате
            if report_format == 'docx':
                from .services import DOCXReportGeneratorService
                docx_service = DOCXReportGeneratorService()
                report_data = docx_service.generate_comparison_report(comparison)
                file_extension = 'docx'
                mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            else:  # pdf
                pdf_service = PDFReportGeneratorService()
                report_data = pdf_service.generate_comparison_report(comparison)
                file_extension = 'pdf'
                mime_type = 'application/pdf'
            
            # Создаем отчет в БД
            report = Report.objects.create(
                user=request.user,
                comparison=comparison,
                title=f"Отчет: {comparison.base_document.title} vs {comparison.compared_document.title}",
                format=report_format,
                file=ContentFile(report_data, name=f"report_{comparison.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.{file_extension}"),
                template_used='default',
                status='ready'
            )
            
            messages.success(request, f'Отчет успешно сгенерирован в формате {report_format.upper()}!')
            return redirect('reports:detail', pk=report.pk)
            
        except Exception as e:
            logger.error(f"Ошибка при генерации отчета для сравнения {comparison.id}: {str(e)}")
            messages.error(request, f'Ошибка при генерации отчета: {str(e)}')
            return redirect('analysis:detail', pk=comparison.pk)


class ReportEmailView(LoginRequiredMixin, View):
    """
    Отправка отчета по email
    """
    
    def get(self, request, pk):
        report = get_object_or_404(Report, pk=pk, user=request.user)
        form = ReportEmailForm()
        return render(request, 'reports/report_email.html', {
            'report': report,
            'form': form
        })
    
    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk, user=request.user)
        form = ReportEmailForm(request.POST)
        
        if form.is_valid():
            recipient_email = form.cleaned_data['recipient_email']
            custom_message = form.cleaned_data['message']
            
            try:
                # Отправляем email
                email_service = EmailReportService()
                result = email_service.send_report_email(report, recipient_email, custom_message)
                
                if result['success']:
                    messages.success(request, 'Отчет успешно отправлен по email!')
                else:
                    messages.warning(request, result['message'])
                
                return redirect('reports:detail', pk=report.pk)
                
            except Exception as e:
                logger.error(f"Ошибка при отправке email для отчета {report.id}: {str(e)}")
                messages.error(request, f'Ошибка при отправке email: {str(e)}')
        
        return render(request, 'reports/report_email.html', {
            'report': report,
            'form': form
        })


class ReportTemplateListView(LoginRequiredMixin, ListView):
    """
    Список шаблонов отчетов
    """
    model = ReportTemplate
    template_name = 'reports/template_list.html'
    context_object_name = 'templates'
    
    def get_queryset(self):
        return ReportTemplate.objects.filter(is_default=True).order_by('name')


class ReportDeleteView(LoginRequiredMixin, DeleteView):
    """
    Удаление отчета
    """
    model = Report
    template_name = 'reports/report_confirm_delete.html'
    
    def get_queryset(self):
        """Показываем только отчеты текущего пользователя"""
        return Report.objects.filter(user=self.request.user)
    
    def get_success_url(self):
        """Перенаправляем на список отчетов"""
        return reverse_lazy('reports:list')
    
    def delete(self, request, *args, **kwargs):
        """
        Переопределяем метод delete для добавления сообщения и обработки файлов
        """
        report = self.get_object()
        report_title = report.title
        report_format = report.get_format_display()
        report_version = report.version
        
        # Удаляем физический файл, если он существует
        if report.file and os.path.exists(report.file.path):
            try:
                os.remove(report.file.path)
                logger.info(f"Deleted physical file: {report.file.path}")
            except OSError as e:
                logger.error(f"Error deleting file {report.file.path}: {str(e)}")
        
        # Проверяем, есть ли другие версии этого отчета
        version_count = report.get_version_count()
        is_latest_version = report.is_latest_version
        
        # Если это была последняя версия и есть другие версии, 
        # делаем предыдущую версию последней
        if is_latest_version and version_count > 1:
            # Находим предыдущую версию
            previous_version = report.get_version_history().exclude(id=report.id).first()
            if previous_version:
                previous_version.is_latest_version = True
                previous_version.save()
                logger.info(f"Made version {previous_version.version} the latest version")
        
        messages.success(request, 
            f'Отчет "{report_title}" ({report_format}) версии {report_version} успешно удален.')
        
        return super().delete(request, *args, **kwargs)


class ReportBulkDeleteView(LoginRequiredMixin, View):
    """
    Массовое удаление выбранных отчетов
    """
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """Удаляет выбранные отчеты"""
        try:
            # Получаем данные из JSON запроса
            data = json.loads(request.body)
            report_ids = data.get('report_ids', [])
            
            if not report_ids:
                return JsonResponse({
                    'success': False,
                    'message': 'Не выбрано ни одного отчета для удаления'
                })
            
            # Получаем отчеты пользователя
            reports = Report.objects.filter(
                id__in=report_ids,
                user=request.user
            )
            
            if not reports.exists():
                return JsonResponse({
                    'success': False,
                    'message': 'Выбранные отчеты не найдены или не принадлежат вам'
                })
            
            # Подсчитываем количество отчетов
            reports_count = reports.count()
            
            # Удаляем отчеты (каскадное удаление позаботится о связанных объектах)
            reports.delete()
            
            logger.info(f"User {request.user.username} bulk deleted {reports_count} reports")
            
            return JsonResponse({
                'success': True,
                'message': f'Успешно удалено {reports_count} отчетов',
                'deleted_count': reports_count
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'Ошибка в формате данных'
            })
        except Exception as e:
            logger.error(f"Error in bulk delete reports by user {request.user.username}: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': f'Ошибка при удалении отчетов: {str(e)}'
            })