"""
Представления для авторизации через Microsoft Active Directory SSO
"""
import logging
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.conf import settings
from django.urls import reverse
from .microsoft_ad_service import MicrosoftADAuthService, MicrosoftADAuthBackend

logger = logging.getLogger(__name__)


def microsoft_ad_login(request):
    """Начать процесс авторизации через Microsoft AD SSO"""
    try:
        # Проверяем, что пользователь не авторизован
        if request.user.is_authenticated:
            return redirect('documents:list')
        
        # Создаем сервис
        ad_service = MicrosoftADAuthService()
        
        # Получаем URL авторизации
        auth_url, state = ad_service.get_auth_url()
        
        # Сохраняем state в сессии
        request.session['microsoft_ad_state'] = state
        
        # Перенаправляем на Microsoft
        return redirect(auth_url)
        
    except ValueError as e:
        messages.error(request, f"Microsoft AD SSO не настроен: {str(e)}")
        return redirect('users:login')
    except Exception as e:
        logger.error(f"Ошибка начала авторизации AD SSO: {e}")
        messages.error(request, "Ошибка авторизации через Microsoft AD")
        return redirect('users:login')


def microsoft_ad_callback(request):
    """Обработка ответа от Microsoft AD SSO"""
    try:
        # Получаем параметры из URL
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')
        
        # Проверяем ошибки
        if error:
            error_description = request.GET.get('error_description', 'Неизвестная ошибка')
            logger.error(f"Ошибка авторизации AD SSO: {error} - {error_description}")
            messages.error(request, f"Ошибка авторизации: {error_description}")
            return redirect('users:login')
        
        # Проверяем обязательные параметры
        if not code or not state:
            messages.error(request, "Неверные параметры авторизации")
            return redirect('users:login')
        
        # Проверяем state
        saved_state = request.session.get('microsoft_ad_state')
        if state != saved_state:
            messages.error(request, "Неверный state параметр")
            return redirect('users:login')
        
        # Создаем сервис
        ad_service = MicrosoftADAuthService()
        
        # Получаем токен
        token_result = ad_service.get_token_from_code(code, state)
        
        # Сохраняем токен в сессии
        request.session['microsoft_ad_access_token'] = token_result['access_token']
        request.session['microsoft_ad_refresh_token'] = token_result.get('refresh_token')
        request.session['microsoft_ad_id_token'] = token_result.get('id_token')
        
        # Получаем информацию о пользователе
        user_info = ad_service.get_user_info(token_result['access_token'])
        
        # Создаем или обновляем пользователя
        user = ad_service.create_or_update_user(user_info)
        
        # Авторизуем пользователя
        login(request, user, backend='settings.microsoft_ad_service.MicrosoftADAuthBackend')
        
        # Очищаем временные данные
        request.session.pop('microsoft_ad_state', None)
        
        messages.success(request, f"Добро пожаловать, {user.get_full_name() or user.username}!")
        
        # Перенаправляем на главную страницу
        return redirect('documents:list')
        
    except Exception as e:
        logger.error(f"Ошибка обработки callback AD SSO: {e}")
        messages.error(request, "Ошибка авторизации через Microsoft AD")
        return redirect('users:login')


def microsoft_ad_logout(request):
    """Выход из системы и отзыв токенов Microsoft AD"""
    try:
        if request.user.is_authenticated:
            # Отзываем токены Microsoft AD
            access_token = request.session.get('microsoft_ad_access_token')
            if access_token:
                try:
                    ad_service = MicrosoftADAuthService()
                    # Здесь можно добавить отзыв токена через Microsoft Graph API
                    pass
                except Exception as e:
                    logger.warning(f"Не удалось отозвать токен AD SSO: {e}")
            
            # Очищаем сессию
            request.session.pop('microsoft_ad_access_token', None)
            request.session.pop('microsoft_ad_refresh_token', None)
            request.session.pop('microsoft_ad_id_token', None)
            
            # Выходим из системы
            logout(request)
            
            messages.success(request, "Вы успешно вышли из системы")
        
        return redirect('users:login')
        
    except Exception as e:
        logger.error(f"Ошибка выхода AD SSO: {e}")
        messages.error(request, "Ошибка при выходе из системы")
        return redirect('users:login')


def microsoft_ad_status(request):
    """Проверить статус авторизации Microsoft AD SSO"""
    try:
        from .models import ApplicationSettings
        settings_obj = ApplicationSettings.get_settings()
        
        if not settings_obj.microsoft_ad_sso_enabled:
            return JsonResponse({
                'enabled': False,
                'message': 'Microsoft AD SSO не включен'
            })
        
        # Проверяем, авторизован ли пользователь через AD SSO
        is_authenticated = request.user.is_authenticated
        has_ad_token = bool(request.session.get('microsoft_ad_access_token'))
        
        return JsonResponse({
            'enabled': True,
            'authenticated': is_authenticated,
            'has_ad_token': has_ad_token,
            'user': {
                'username': request.user.username if is_authenticated else None,
                'email': request.user.email if is_authenticated else None,
                'full_name': request.user.get_full_name() if is_authenticated else None
            } if is_authenticated else None
        })
        
    except Exception as e:
        logger.error(f"Ошибка проверки статуса AD SSO: {e}")
        return JsonResponse({
            'error': str(e)
        }, status=500)


def microsoft_ad_test(request):
    """Тестировать соединение с Microsoft AD SSO"""
    try:
        from .models import ApplicationSettings
        settings_obj = ApplicationSettings.get_settings()
        
        if not settings_obj.microsoft_ad_sso_enabled:
            return JsonResponse({
                'success': False,
                'message': 'Microsoft AD SSO не включен в настройках'
            })
        
        # Создаем сервис и тестируем соединение
        ad_service = MicrosoftADAuthService()
        success, message = ad_service.test_connection()
        
        return JsonResponse({
            'success': success,
            'message': message
        })
        
    except Exception as e:
        logger.error(f"Ошибка тестирования AD SSO: {e}")
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)


def microsoft_ad_disable(request):
    """Отключить авторизацию Microsoft AD SSO для текущего пользователя"""
    try:
        if request.user.is_authenticated:
            # Очищаем токены из сессии
            request.session.pop('microsoft_ad_access_token', None)
            request.session.pop('microsoft_ad_refresh_token', None)
            request.session.pop('microsoft_ad_id_token', None)
            
            messages.success(request, "Авторизация Microsoft AD SSO отключена")
        
        return redirect('users:login')
        
    except Exception as e:
        logger.error(f"Ошибка отключения AD SSO: {e}")
        messages.error(request, "Ошибка при отключении авторизации")
        return redirect('users:login')


def microsoft_ad_login_page(request):
    """Страница входа через Microsoft AD SSO"""
    try:
        from .models import ApplicationSettings
        settings_obj = ApplicationSettings.get_settings()
        
        if not settings_obj.microsoft_ad_sso_enabled:
            messages.error(request, "Microsoft AD SSO не включен в настройках")
            return redirect('users:login')
        
        context = {
            'microsoft_ad_enabled': True,
            'domain': settings_obj.microsoft_ad_sso_domain,
            'title': 'Вход через Microsoft Active Directory'
        }
        
        return render(request, 'registration/microsoft_ad_login.html', context)
        
    except Exception as e:
        logger.error(f"Ошибка отображения страницы AD SSO: {e}")
        messages.error(request, "Ошибка загрузки страницы входа")
        return redirect('users:login')
