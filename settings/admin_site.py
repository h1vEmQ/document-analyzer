from django.contrib.admin import AdminSite
from django.contrib.admin.views.main import ChangeList
from django.shortcuts import render
from django.urls import path
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.admin.views.decorators import staff_member_required
from .models import ApplicationSettings, ServerSettings
from .forms import ApplicationSettingsForm, ServerSettingsForm
# from .views import server_settings_view, reset_server_settings, server_health_view, server_metrics_view
import json


class WARAAdminSite(AdminSite):
    """Кастомная администрирование 📊 Анализатор документов с интеграцией настроек"""
    
    site_header = '📊 Анализатор документов Администрирование'
    site_title = '📊 Анализатор документов'
    index_title = 'Управление системой анализа документов'
    
    def get_urls(self):
        """Добавляем кастомные URL для настроек"""
        urls = super().get_urls()
        custom_urls = [
            path('settings/', self.admin_view(self.settings_view), name='settings'),
            path('settings/reset/', self.admin_view(self.reset_settings), name='settings_reset'),
            # path('server-settings/', self.admin_view(self.server_settings_view), name='server_settings'),
            # path('server-settings/reset/', self.admin_view(self.reset_server_settings), name='server_settings_reset'),
            # path('server-health/', self.admin_view(self.server_health_view), name='server_health'),
            # path('server-metrics/', self.admin_view(self.server_metrics_view), name='server_metrics'),
        ]
        
        # Добавляем URL для Microsoft Graph
        from .microsoft_urls import urlpatterns as microsoft_urls
        custom_urls.extend(microsoft_urls)
        return custom_urls + urls
    
    @staff_member_required
    def settings_view(self, request):
        """Кастомное представление страницы настроек"""
        settings = ApplicationSettings.get_settings()
        
        if request.method == 'POST':
            form = ApplicationSettingsForm(request.POST, instance=settings, user=request.user)
            if form.is_valid():
                form.instance.updated_by = request.user
                form.save()
                messages.success(request, 'Настройки успешно сохранены!')
                return HttpResponseRedirect(request.path)
            else:
                messages.error(request, 'Ошибка при сохранении настроек. Проверьте введенные данные.')
        else:
            form = ApplicationSettingsForm(instance=settings, user=request.user)
        
        context = {
            'form': form,
            'settings': settings,
            'title': 'Настройки приложения',
            'site_header': self.site_header,
            'site_title': self.site_title,
            'has_permission': True,
            'user': request.user,
            'opts': ApplicationSettings._meta,
        }
        
        return render(request, 'admin/settings.html', context)
    
    @staff_member_required
    def reset_settings(self, request):
        """Сброс настроек к значениям по умолчанию"""
        if request.method == 'POST':
            settings = ApplicationSettings.get_settings()
            
            # Сброс к значениям по умолчанию
            settings.app_name = '📊 Анализатор документов'
            settings.app_description = 'Система анализа документов'
            settings.max_file_size = 10485760  # 10MB
            settings.allowed_file_types = 'docx,pdf'
            settings.auto_analysis_enabled = True
            settings.analysis_timeout = 300
            settings.default_neural_network_model = 'llama3'
            settings.auto_reports_enabled = True
            settings.default_report_format = 'pdf'
            settings.email_notifications_enabled = False
            settings.notification_email = ''
            settings.session_timeout = 3600
            settings.max_login_attempts = 5
            settings.updated_by = request.user
            settings.save()
            
            messages.success(request, 'Настройки сброшены к значениям по умолчанию!')
            return HttpResponseRedirect('/admin/settings/')
        
        # GET запрос - показываем страницу подтверждения
        context = {
            'title': 'Сброс настроек',
            'site_header': self.site_header,
            'site_title': self.site_title,
            'has_permission': True,
        }
        return render(request, 'admin/settings_reset.html', context)
    
    # def server_settings_view(self, request):
    #     """Представление настроек сервера"""
    #     return server_settings_view(request)
    
    # def reset_server_settings(self, request):
    #     """Сброс настроек сервера"""
    #     return reset_server_settings(request)
    
    # def server_health_view(self, request):
    #     """Представление состояния сервера"""
    #     return server_health_view(request)
    
    # def server_metrics_view(self, request):
    #     """Представление метрик сервера"""
    #     return server_metrics_view(request)
    
    def index(self, request, extra_context=None):
        """Переопределяем главную страницу админки для добавления ссылки на настройки"""
        extra_context = extra_context or {}
        extra_context['show_settings_link'] = True
        return super().index(request, extra_context)


# Создаем экземпляр кастомной админ-панели
admin_site = WARAAdminSite(name='analyzer_admin')

# Регистрируем все модели в кастомной админ-панели
from django.contrib.auth.models import User, Group
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session

# Регистрируем стандартные модели Django
admin_site.register(User)
admin_site.register(Group)
admin_site.register(ContentType)
admin_site.register(Session)

# Регистрируем модели приложений Анализатор документов
from documents.models import Document
from analysis.models import Comparison, Change, AnalysisSettings
from reports.models import Report, ReportTemplate, EmailNotification

admin_site.register(Document)
admin_site.register(Comparison)
admin_site.register(Change)
admin_site.register(AnalysisSettings)
admin_site.register(Report)
admin_site.register(ReportTemplate)
admin_site.register(EmailNotification)
admin_site.register(ApplicationSettings)
admin_site.register(ServerSettings)
