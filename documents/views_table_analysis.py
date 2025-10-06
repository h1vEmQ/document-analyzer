from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.views import View
from django.http import JsonResponse
from .models import Document
from .services import DocumentTableAnalysisService
import logging

logger = logging.getLogger(__name__)


class DocumentAnalyzeTablesView(LoginRequiredMixin, View):
    """
    AJAX endpoint для анализа таблиц документа
    """
    
    def post(self, request, pk):
        """
        POST запрос для анализа таблиц
        """
        try:
            document = get_object_or_404(Document, pk=pk, user=request.user)
            
            # Проверяем, что документ обработан
            if document.status != 'processed':
                return JsonResponse({
                    'success': False,
                    'error': 'Документ должен быть обработан перед анализом таблиц'
                }, status=400)
            
            # Проверяем, что есть содержимое
            if not document.has_content():
                return JsonResponse({
                    'success': False,
                    'error': 'Документ не содержит извлеченного содержимого'
                }, status=400)
            
            # Анализируем таблицы
            table_analysis_service = DocumentTableAnalysisService()
            result = table_analysis_service.analyze_document_tables(document)
            
            if result['success']:
                return JsonResponse({
                    'success': True,
                    'message': 'Анализ таблиц успешно выполнен',
                    'tables_count': result.get('tables_count', 0),
                    'summary': result.get('summary', {}),
                    'document_id': document.id,
                    'document_title': document.title
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': result.get('error', 'Неизвестная ошибка при анализе')
                }, status=500)
                
        except Document.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Документ не найден'
            }, status=404)
        except Exception as e:
            logger.error(f"Ошибка при анализе таблиц документа {pk}: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': 'Внутренняя ошибка сервера'
            }, status=500)
