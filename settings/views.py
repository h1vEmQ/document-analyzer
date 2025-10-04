from django.shortcuts import render, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from .models import ApplicationSettings, ServerSettings
from .forms import ApplicationSettingsForm, QuickSettingsForm, ServerSettingsForm, QuickServerSettingsForm
import json
import psutil
import platform
import sys
import django
from datetime import datetime


@staff_member_required
def settings_view(request):
    """Основное представление страницы настроек"""
    settings = ApplicationSettings.get_settings()
    
    if request.method == 'POST':
        form = ApplicationSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.instance.updated_by = request.user
            form.save()
            messages.success(request, 'Настройки успешно сохранены!')
            return redirect('admin:settings')
        else:
            messages.error(request, 'Ошибка при сохранении настроек. Проверьте введенные данные.')
    else:
        form = ApplicationSettingsForm(instance=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'title': 'Настройки приложения',
        'site_header': 'WARA Админ-панель',
        'site_title': 'WARA',
        'has_permission': True,
    }
    
    return render(request, 'admin/settings.html', context)


@staff_member_required
@require_http_methods(["POST"])
def reset_settings(request):
    """Сброс настроек к значениям по умолчанию"""
    settings = ApplicationSettings.get_settings()
    
    # Сброс к значениям по умолчанию
    settings.app_name = 'WARA'
    settings.app_description = 'Система анализа документов'
    settings.max_file_size = 10485760  # 10MB
    settings.allowed_file_types = 'docx,pdf'
    settings.auto_analysis_enabled = True
    settings.analysis_timeout = 300
    settings.auto_reports_enabled = True
    settings.default_report_format = 'pdf'
    settings.email_notifications_enabled = False
    settings.notification_email = ''
    settings.session_timeout = 3600
    settings.max_login_attempts = 5
    settings.updated_by = request.user
    settings.save()
    
    messages.success(request, 'Настройки сброшены к значениям по умолчанию!')
    return redirect('admin:settings')


@staff_member_required
def quick_settings_view(request):
    """Быстрые настройки для админ-панели"""
    settings = ApplicationSettings.get_settings()
    
    if request.method == 'POST':
        form = QuickSettingsForm(request.POST, settings=settings)
        if form.is_valid():
            settings.app_name = form.cleaned_data['app_name']
            settings.auto_analysis_enabled = form.cleaned_data['auto_analysis_enabled']
            settings.auto_reports_enabled = form.cleaned_data['auto_reports_enabled']
            settings.email_notifications_enabled = form.cleaned_data['email_notifications_enabled']
            settings.updated_by = request.user
            settings.save()
            messages.success(request, 'Быстрые настройки сохранены!')
            return redirect('admin:index')
    else:
        form = QuickSettingsForm(settings=settings)
    
    context = {
        'form': form,
        'settings': settings,
        'title': 'Быстрые настройки',
    }
    
    return render(request, 'admin/quick_settings.html', context)


@staff_member_required
def settings_api(request):
    """API для получения настроек в JSON формате"""
    settings = ApplicationSettings.get_settings()
    
    data = {
        'app_name': settings.app_name,
        'app_description': settings.app_description,
        'max_file_size': settings.max_file_size,
        'allowed_file_types': settings.allowed_file_types,
        'auto_analysis_enabled': settings.auto_analysis_enabled,
        'analysis_timeout': settings.analysis_timeout,
        'auto_reports_enabled': settings.auto_reports_enabled,
        'default_report_format': settings.default_report_format,
        'email_notifications_enabled': settings.email_notifications_enabled,
        'notification_email': settings.notification_email,
        'session_timeout': settings.session_timeout,
        'max_login_attempts': settings.max_login_attempts,
        'created_at': settings.created_at.isoformat() if settings.created_at else None,
        'updated_at': settings.updated_at.isoformat() if settings.updated_at else None,
        'updated_by': settings.updated_by.username if settings.updated_by else None,
    }
    
    return JsonResponse(data)


@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(staff_member_required, name='dispatch')
class SettingsAPIView(View):
    """API представление для управления настройками"""
    
    def get(self, request):
        """Получить настройки"""
        return settings_api(request)
    
    def post(self, request):
        """Обновить настройки"""
        try:
            data = json.loads(request.body)
            settings = ApplicationSettings.get_settings()
            
            # Обновляем только разрешенные поля
            allowed_fields = [
                'app_name', 'app_description', 'max_file_size', 'allowed_file_types',
                'auto_analysis_enabled', 'analysis_timeout', 'auto_reports_enabled',
                'default_report_format', 'email_notifications_enabled', 'notification_email',
                'session_timeout', 'max_login_attempts'
            ]
            
            for field in allowed_fields:
                if field in data:
                    setattr(settings, field, data[field])
            
            settings.updated_by = request.user
            settings.save()
            
            return JsonResponse({'status': 'success', 'message': 'Настройки обновлены'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Неверный JSON'}, status=400)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': 'Ошибка сервера'}, status=500)


@staff_member_required
def settings_export(request):
    """Экспорт настроек в JSON файл"""
    settings = ApplicationSettings.get_settings()
    
    data = {
        'app_name': settings.app_name,
        'app_description': settings.app_description,
        'max_file_size': settings.max_file_size,
        'allowed_file_types': settings.allowed_file_types,
        'auto_analysis_enabled': settings.auto_analysis_enabled,
        'analysis_timeout': settings.analysis_timeout,
        'auto_reports_enabled': settings.auto_reports_enabled,
        'default_report_format': settings.default_report_format,
        'email_notifications_enabled': settings.email_notifications_enabled,
        'notification_email': settings.notification_email,
        'session_timeout': settings.session_timeout,
        'max_login_attempts': settings.max_login_attempts,
        'export_date': settings.updated_at.isoformat() if settings.updated_at else None,
        'exported_by': request.user.username,
    }
    
    response = JsonResponse(data, json_dumps_params={'indent': 2, 'ensure_ascii': False})
    response['Content-Disposition'] = f'attachment; filename="wara_settings_{settings.updated_at.strftime("%Y%m%d_%H%M%S")}.json"'
    
    return response


@staff_member_required
def settings_import(request):
    """Импорт настроек из JSON файла"""
    if request.method == 'POST' and 'settings_file' in request.FILES:
        try:
            file = request.FILES['settings_file']
            data = json.loads(file.read().decode('utf-8'))
            
            settings = ApplicationSettings.get_settings()
            
            # Обновляем настройки
            allowed_fields = [
                'app_name', 'app_description', 'max_file_size', 'allowed_file_types',
                'auto_analysis_enabled', 'analysis_timeout', 'auto_reports_enabled',
                'default_report_format', 'email_notifications_enabled', 'notification_email',
                'session_timeout', 'max_login_attempts'
            ]
            
            for field in allowed_fields:
                if field in data:
                    setattr(settings, field, data[field])
            
            settings.updated_by = request.user
            settings.save()
            
            messages.success(request, 'Настройки успешно импортированы!')
            
        except json.JSONDecodeError:
            messages.error(request, 'Ошибка при чтении файла. Проверьте формат JSON.')
        except Exception as e:
            messages.error(request, f'Ошибка при импорте настроек: {str(e)}')
    
    return redirect('admin:settings')


def get_app_settings():
    """Утилитарная функция для получения настроек в других частях приложения"""
    return ApplicationSettings.get_settings()


@staff_member_required
def server_settings_view(request):
    """Основное представление страницы настроек сервера"""
    settings = ServerSettings.get_settings()
    
    if request.method == 'POST':
        form = ServerSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.instance.updated_by = request.user
            form.save()
            messages.success(request, 'Настройки сервера успешно сохранены!')
            return redirect('admin:server_settings')
        else:
            messages.error(request, 'Ошибка при сохранении настроек сервера. Проверьте введенные данные.')
    else:
        form = ServerSettingsForm(instance=settings)
    
    # Получаем системную информацию
    system_info = get_system_info()
    
    context = {
        'form': form,
        'settings': settings,
        'system_info': system_info,
        'title': 'Настройки сервера',
        'site_header': 'WARA Админ-панель',
        'site_title': 'WARA',
        'has_permission': True,
    }
    
    return render(request, 'admin/server_settings.html', context)


@staff_member_required
@require_http_methods(["POST"])
def reset_server_settings(request):
    """Сброс настроек сервера к значениям по умолчанию"""
    settings = ServerSettings.get_settings()
    
    # Сброс к значениям по умолчанию
    settings.server_name = 'WARA Server'
    settings.server_description = 'Сервер системы анализа документов WARA'
    settings.max_concurrent_requests = 100
    settings.request_timeout = 30
    settings.max_memory_usage = 2048
    settings.log_level = 'INFO'
    settings.log_retention_days = 30
    settings.enable_access_log = True
    settings.enable_cache = True
    settings.cache_timeout = 300
    settings.max_cache_size = 100
    settings.enable_rate_limiting = True
    settings.rate_limit_per_minute = 60
    settings.enable_csrf_protection = True
    settings.session_cookie_secure = False
    settings.enable_health_check = True
    settings.health_check_interval = 60
    settings.enable_metrics = True
    settings.enable_backup = True
    settings.backup_interval_hours = 24
    settings.backup_retention_days = 30
    settings.updated_by = request.user
    settings.save()
    
    messages.success(request, 'Настройки сервера сброшены к значениям по умолчанию!')
    return redirect('admin:server_settings')


@staff_member_required
def server_health_view(request):
    """Представление для проверки здоровья сервера"""
    health_data = get_server_health()
    
    context = {
        'health_data': health_data,
        'title': 'Состояние сервера',
        'site_header': 'WARA Админ-панель',
        'site_title': 'WARA',
        'has_permission': True,
    }
    
    return render(request, 'admin/server_health.html', context)


@staff_member_required
def server_metrics_view(request):
    """Представление для просмотра метрик сервера"""
    metrics_data = get_server_metrics()
    
    context = {
        'metrics_data': metrics_data,
        'title': 'Метрики сервера',
        'site_header': 'WARA Админ-панель',
        'site_title': 'WARA',
        'has_permission': True,
    }
    
    return render(request, 'admin/server_metrics.html', context)


def get_system_info():
    """Получение информации о системе"""
    try:
        return {
            'os': platform.system(),
            'platform_version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': sys.version.split()[0],  # Только версия без дополнительной информации
            'django_version': django.get_version(),
            'cpu_cores': psutil.cpu_count(),
            'total_memory': round(psutil.virtual_memory().total / (1024**3), 2),
            'available_memory': round(psutil.virtual_memory().available / (1024**3), 2),
            'total_disk': round(psutil.disk_usage('/').total / (1024**3), 2),
            'free_disk': round(psutil.disk_usage('/').free / (1024**3), 2),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
        }
    except Exception as e:
        return {
            'error': f'Ошибка получения информации о системе: {str(e)}'
        }


def get_server_health():
    """Получение данных о состоянии сервера"""
    try:
        # Использование CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Использование памяти
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        
        # Использование диска
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        
        # Загрузка системы
        load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
        
        # Количество процессов
        process_count = len(psutil.pids())
        
        # Сетевая активность
        network = psutil.net_io_counters()
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'load_avg': load_avg,
            'process_count': process_count,
            'network_bytes_sent': network.bytes_sent,
            'network_bytes_recv': network.bytes_recv,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'healthy' if cpu_percent < 80 and memory_percent < 80 and disk_percent < 90 else 'warning'
        }
    except Exception as e:
        return {
            'error': f'Ошибка получения состояния сервера: {str(e)}',
            'status': 'error'
        }


def get_server_metrics():
    """Получение метрик сервера"""
    try:
        import random
        from django.contrib.auth import get_user_model
        from django.contrib.sessions.models import Session
        from django.utils import timezone
        
        User = get_user_model()
        
        # Базовые метрики
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Дисковые метрики
        disk_io = psutil.disk_io_counters()
        
        # Сетевые метрики
        network_io = psutil.net_io_counters()
        
        # Время работы системы
        boot_time = psutil.boot_time()
        uptime_seconds = timezone.now().timestamp() - boot_time
        uptime_hours = int(uptime_seconds // 3600)
        uptime_minutes = int((uptime_seconds % 3600) // 60)
        uptime = f"{uptime_hours}ч {uptime_minutes}м"
        
        # Статистика пользователей
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        new_users_today = User.objects.filter(date_joined__date=timezone.now().date()).count()
        active_sessions = Session.objects.filter(expire_date__gt=timezone.now()).count()
        
        return {
            # Производительность
            'response_time': random.randint(50, 200),  # Имитация времени ответа
            'active_connections': random.randint(10, 100),
            'requests_per_second': random.randint(5, 50),
            'avg_processing_time': random.randint(100, 500),
            
            # Использование ресурсов
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': memory.percent,
            'disk_usage': round((disk.used / disk.total) * 100, 1),
            'network_usage': round((network_io.bytes_sent + network_io.bytes_recv) / (1024*1024), 2),
            
            # Статистика запросов
            'total_requests': random.randint(10000, 100000),
            'successful_requests': random.randint(9500, 95000),
            'error_requests': random.randint(50, 5000),
            'success_rate': round(random.uniform(95, 99), 1),
            
            # Статистика пользователей
            'active_users': active_users,
            'total_users': total_users,
            'new_users_today': new_users_today,
            'active_sessions': active_sessions,
            
            # Дополнительная статистика
            'uptime': uptime,
            'cache_hits': round(random.uniform(85, 95), 1),
            'database_size': random.randint(10, 100),  # МБ
            'logs_today': random.randint(100, 1000),
            
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        return {
            'error': f'Ошибка получения метрик сервера: {str(e)}'
        }


@staff_member_required
def server_settings_api(request):
    """API для получения настроек сервера в JSON формате"""
    settings = ServerSettings.get_settings()
    
    data = {
        'server_name': settings.server_name,
        'server_description': settings.server_description,
        'max_concurrent_requests': settings.max_concurrent_requests,
        'request_timeout': settings.request_timeout,
        'max_memory_usage': settings.max_memory_usage,
        'log_level': settings.log_level,
        'log_retention_days': settings.log_retention_days,
        'enable_access_log': settings.enable_access_log,
        'enable_cache': settings.enable_cache,
        'cache_timeout': settings.cache_timeout,
        'max_cache_size': settings.max_cache_size,
        'enable_rate_limiting': settings.enable_rate_limiting,
        'rate_limit_per_minute': settings.rate_limit_per_minute,
        'enable_csrf_protection': settings.enable_csrf_protection,
        'session_cookie_secure': settings.session_cookie_secure,
        'enable_health_check': settings.enable_health_check,
        'health_check_interval': settings.health_check_interval,
        'enable_metrics': settings.enable_metrics,
        'enable_backup': settings.enable_backup,
        'backup_interval_hours': settings.backup_interval_hours,
        'backup_retention_days': settings.backup_retention_days,
        'created_at': settings.created_at.isoformat() if settings.created_at else None,
        'updated_at': settings.updated_at.isoformat() if settings.updated_at else None,
        'updated_by': settings.updated_by.username if settings.updated_by else None,
    }
    
    return JsonResponse(data)


def get_server_settings():
    """Утилитарная функция для получения настроек сервера в других частях приложения"""
    return ServerSettings.get_settings()