"""
Представления для работы с Microsoft Graph API
"""
import json
import logging
from urllib.parse import urlencode, parse_qs
from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.conf import settings
from .microsoft_graph_service import MicrosoftGraphService
from .models import MicrosoftGraphToken

logger = logging.getLogger(__name__)


@login_required
def microsoft_auth_start(request):
    """Начать процесс авторизации с Microsoft Graph"""
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            messages.error(request, 'Интеграция с Microsoft Graph не включена')
            return redirect('admin:settings')
        
        # Получаем URL для авторизации
        auth_url = graph_service.get_auth_url(str(request.user.id))
        
        # Перенаправляем пользователя на Microsoft
        return redirect(auth_url)
        
    except Exception as e:
        logger.error(f"Ошибка начала авторизации Microsoft Graph: {str(e)}")
        messages.error(request, f'Ошибка начала авторизации: {str(e)}')
        return redirect('admin:settings')


@require_http_methods(["GET"])
def microsoft_auth_callback(request):
    """Обработка ответа авторизации от Microsoft"""
    try:
        # Получаем параметры из URL
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        error_description = request.GET.get('error_description')
        
        if error:
            logger.error(f"Ошибка авторизации Microsoft: {error} - {error_description}")
            messages.error(request, f'Ошибка авторизации: {error_description or error}')
            return redirect('admin:settings')
        
        if not code or not state:
            messages.error(request, 'Неполные параметры авторизации')
            return redirect('admin:settings')
        
        # Парсим state для получения user_id
        try:
            state_data = json.loads(state)
            user_id = state_data.get('user_id')
        except (json.JSONDecodeError, KeyError):
            messages.error(request, 'Некорректные параметры состояния')
            return redirect('admin:settings')
        
        # Проверяем, что user_id соответствует текущему пользователю
        if str(request.user.id) != str(user_id):
            messages.error(request, 'Несоответствие пользователя')
            return redirect('admin:settings')
        
        # Получаем токен доступа
        graph_service = MicrosoftGraphService()
        token_result = graph_service.get_token_from_code(code, str(request.user.id))
        
        messages.success(request, 'Успешная авторизация с Microsoft Graph!')
        logger.info(f"Пользователь {request.user.username} успешно авторизовался в Microsoft Graph")
        
        return redirect('admin:microsoft_test')
        
    except Exception as e:
        logger.error(f"Ошибка обработки ответа авторизации: {str(e)}")
        messages.error(request, f'Ошибка обработки авторизации: {str(e)}')
        return redirect('admin:settings')


@login_required
def microsoft_auth_status(request):
    """Проверить статус авторизации с Microsoft Graph"""
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            return JsonResponse({
                'success': False,
                'error': 'Интеграция с Microsoft Graph не включена'
            })
        
        # Проверяем наличие токена
        token = graph_service.get_valid_token(str(request.user.id))
        
        if token:
            # Получаем информацию о токене
            try:
                token_obj = MicrosoftGraphToken.objects.get(user=request.user)
                return JsonResponse({
                    'success': True,
                    'authorized': True,
                    'expires_at': token_obj.expires_at.isoformat(),
                    'scope': token_obj.scope
                })
            except MicrosoftGraphToken.DoesNotExist:
                pass
        
        return JsonResponse({
            'success': True,
            'authorized': False
        })
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса авторизации: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def microsoft_test_connection(request):
    """Тестировать соединение с Microsoft Graph"""
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            messages.error(request, 'Интеграция с Microsoft Graph не включена')
            return redirect('admin:settings')
        
        # Тестируем соединение
        result = graph_service.test_connection(str(request.user.id))
        
        if result['success']:
            messages.success(request, f'Соединение успешно! Пользователь: {result["user"]["display_name"]}')
        else:
            messages.error(request, f'Ошибка соединения: {result["error"]}')
        
        return redirect('admin:settings')
        
    except Exception as e:
        logger.error(f"Ошибка тестирования соединения: {str(e)}")
        messages.error(request, f'Ошибка тестирования: {str(e)}')
        return redirect('admin:settings')


@login_required
def microsoft_documents_list(request):
    """Получить список документов из SharePoint"""
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            return JsonResponse({
                'success': False,
                'error': 'Интеграция с Microsoft Graph не включена'
            })
        
        # Получаем список документов
        documents = graph_service.list_documents(str(request.user.id))
        
        return JsonResponse({
            'success': True,
            'documents': documents
        })
        
    except Exception as e:
        logger.error(f"Ошибка получения списка документов: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def microsoft_document_download(request, document_id):
    """Скачать документ из SharePoint"""
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            messages.error(request, 'Интеграция с Microsoft Graph не включена')
            return redirect('documents:list')
        
        # Скачиваем документ
        file_content = graph_service.download_document(str(request.user.id), document_id)
        
        # Определяем имя файла
        file_name = f"sharepoint_document_{document_id}.docx"
        
        # Возвращаем файл
        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        
        return response
        
    except Exception as e:
        logger.error(f"Ошибка скачивания документа: {str(e)}")
        messages.error(request, f'Ошибка скачивания документа: {str(e)}')
        return redirect('documents:list')


@login_required
@csrf_exempt
def microsoft_upload_document(request):
    """Загрузить документ в SharePoint"""
    if request.method != 'POST':
        return JsonResponse({
            'success': False,
            'error': 'Метод не поддерживается'
        })
    
    try:
        graph_service = MicrosoftGraphService()
        
        if not graph_service.is_enabled:
            return JsonResponse({
                'success': False,
                'error': 'Интеграция с Microsoft Graph не включена'
            })
        
        # Получаем файл из запроса
        if 'file' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Файл не найден'
            })
        
        file = request.FILES['file']
        
        # Читаем содержимое файла
        file_content = file.read()
        
        # Загружаем документ
        result = graph_service.upload_document(
            str(request.user.id),
            file_content,
            file.name
        )
        
        return JsonResponse({
            'success': True,
            'document': result
        })
        
    except Exception as e:
        logger.error(f"Ошибка загрузки документа: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        })


@login_required
def microsoft_disconnect(request):
    """Отключить авторизацию с Microsoft Graph"""
    try:
        # Удаляем токен из базы данных
        MicrosoftGraphToken.objects.filter(user=request.user).delete()
        
        messages.success(request, 'Авторизация с Microsoft Graph отключена')
        logger.info(f"Пользователь {request.user.username} отключил авторизацию Microsoft Graph")
        
        return redirect('admin:settings')
        
    except Exception as e:
        logger.error(f"Ошибка отключения авторизации: {str(e)}")
        messages.error(request, f'Ошибка отключения: {str(e)}')
        return redirect('admin:settings')
