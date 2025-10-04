from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from .admin_forms import AdminUserCreateForm, AdminUserEditForm
from documents.models import Document
from analysis.models import Comparison
from reports.models import Report
from settings.models import ServerSettings, ApplicationSettings
from settings.forms import ServerSettingsForm, ApplicationSettingsForm
from settings.views import get_system_info, get_server_health, get_server_metrics
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


class AdminRequiredMixin(UserPassesTestMixin):
    """
    Миксин для проверки прав администратора
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.role == 'admin'
        )
    
    def handle_no_permission(self):
        messages.error(self.request, 'У вас нет прав для доступа к этой странице.')
        return redirect('documents:list')


class AdminUserListView(AdminRequiredMixin, ListView):
    """
    Список всех пользователей для администратора
    """
    model = User
    template_name = 'users/admin/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        """Возвращаем всех пользователей с дополнительной информацией"""
        queryset = User.objects.all().select_related().prefetch_related(
            'documents',
            'comparisons',
            'reports'
        )
        
        # Фильтрация по поисковому запросу
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                Q(username__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query)
            )
        
        # Фильтрация по роли
        role_filter = self.request.GET.get('role')
        if role_filter:
            if role_filter == 'admin':
                queryset = queryset.filter(Q(is_superuser=True) | Q(role='admin'))
            elif role_filter == 'viewer':
                queryset = queryset.filter(is_superuser=False, role='viewer')
            elif role_filter == 'manager':
                queryset = queryset.filter(role='manager')
        
        # Фильтрация по статусу
        status_filter = self.request.GET.get('status')
        if status_filter == 'active':
            queryset = queryset.filter(is_active=True)
        elif status_filter == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-date_joined')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Статистика пользователей
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        admin_users = User.objects.filter(Q(is_superuser=True) | Q(role='admin')).count()
        
        # Пользователи, зарегистрированные за последние 30 дней
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        
        context.update({
            'total_users': total_users,
            'active_users': active_users,
            'admin_users': admin_users,
            'recent_users': recent_users,
            'search_query': self.request.GET.get('search', ''),
            'role_filter': self.request.GET.get('role', ''),
            'status_filter': self.request.GET.get('status', ''),
        })
        
        return context


class AdminUserDetailView(AdminRequiredMixin, DetailView):
    """
    Детальный просмотр пользователя для администратора
    """
    model = User
    template_name = 'users/admin/user_detail.html'
    context_object_name = 'user_obj'
    
    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_obj = self.get_object()
        
        # Статистика пользователя
        documents_count = Document.objects.filter(user=user_obj).count()
        comparisons_count = Comparison.objects.filter(user=user_obj).count()
        reports_count = Report.objects.filter(user=user_obj).count()
        
        # Последняя активность
        last_login = user_obj.last_login
        date_joined = user_obj.date_joined
        
        # Документы пользователя (последние 10)
        recent_documents = Document.objects.filter(user=user_obj).order_by('-upload_date')[:10]
        
        # Сравнения пользователя (последние 10)
        recent_comparisons = Comparison.objects.filter(user=user_obj).order_by('-created_date')[:10]
        
        # Отчеты пользователя (последние 10)
        recent_reports = Report.objects.filter(user=user_obj).order_by('-generated_date')[:10]
        
        context.update({
            'documents_count': documents_count,
            'comparisons_count': comparisons_count,
            'reports_count': reports_count,
            'last_login': last_login,
            'date_joined': date_joined,
            'recent_documents': recent_documents,
            'recent_comparisons': recent_comparisons,
            'recent_reports': recent_reports,
        })
        
        return context


class AdminUserCreateView(AdminRequiredMixin, CreateView):
    """
    Создание нового пользователя администратором
    """
    model = User
    form_class = AdminUserCreateForm
    template_name = 'users/admin/user_create.html'
    success_url = reverse_lazy('users:admin_list')
    
    def form_valid(self, form):
        """Переопределяем для установки пароля и отправки сообщения"""
        user = form.save(commit=False)
        password = form.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        
        user.save()
        
        messages.success(self.request, 
            f'Пользователь "{user.username}" успешно создан.')
        
        logger.info(f"Admin {self.request.user.username} created user {user.username}")
        
        return redirect(self.success_url)


class AdminUserEditView(AdminRequiredMixin, UpdateView):
    """
    Редактирование пользователя администратором
    """
    model = User
    form_class = AdminUserEditForm
    template_name = 'users/admin/user_edit.html'
    context_object_name = 'user_obj'
    
    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])
    
    def get_success_url(self):
        return reverse_lazy('users:admin_detail', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        """Переопределяем для обработки пароля и отправки сообщения"""
        user = form.save(commit=False)
        
        # Обработка пароля
        password = form.cleaned_data.get('new_password')
        if password:
            user.set_password(password)
            messages.info(self.request, 'Пароль пользователя обновлен.')
        
        user.save()
        
        messages.success(self.request, 
            f'Пользователь "{user.username}" успешно обновлен.')
        
        logger.info(f"Admin {self.request.user.username} updated user {user.username}")
        
        return redirect(self.get_success_url())


class AdminUserDeleteView(AdminRequiredMixin, DeleteView):
    """
    Удаление пользователя администратором
    """
    model = User
    template_name = 'users/admin/user_confirm_delete.html'
    success_url = reverse_lazy('users:admin_list')
    
    def get_object(self):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        
        # Нельзя удалить самого себя
        if user == self.request.user:
            messages.error(self.request, 'Нельзя удалить самого себя.')
            return None
        
        return user
    
    def delete(self, request, *args, **kwargs):
        """Переопределяем для добавления сообщения"""
        user = self.get_object()
        if user is None:
            return redirect(self.success_url)
        
        username = user.username
        
        # Подсчитываем связанные объекты
        documents_count = user.documents.count()
        comparisons_count = user.comparisons.count()
        reports_count = user.reports.count()
        
        # Удаляем пользователя (каскадное удаление)
        user.delete()
        
        messages.success(request, 
            f'Пользователь "{username}" и все связанные данные удалены. '
            f'Удалено: {documents_count} документов, {comparisons_count} сравнений, {reports_count} отчетов.')
        
        logger.info(f"Admin {request.user.username} deleted user {username}")
        
        return redirect(self.success_url)


class AdminUserToggleActiveView(AdminRequiredMixin, View):
    """
    Включение/отключение пользователя
    """
    
    def get(self, request, *args, **kwargs):
        user = get_object_or_404(User, pk=self.kwargs['pk'])
        
        # Нельзя отключить самого себя
        if user == request.user:
            messages.error(request, 'Нельзя отключить самого себя.')
            return redirect('users:admin_detail', pk=user.pk)
        
        # Переключаем статус активности
        user.is_active = not user.is_active
        user.save()
        
        status_text = 'активирован' if user.is_active else 'деактивирован'
        messages.success(request, f'Пользователь "{user.username}" {status_text}.')
        
        logger.info(f"Admin {request.user.username} toggled active status for user {user.username} to {user.is_active}")
        
        return redirect('users:admin_list')


class AdminApplicationSettingsView(AdminRequiredMixin, CreateView):
    """
    Настройки приложения для администратора
    """
    model = ApplicationSettings
    form_class = ApplicationSettingsForm
    template_name = 'users/admin/application_settings.html'
    
    def get_object(self):
        return ApplicationSettings.get_settings()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        form.save()
        messages.success(self.request, 'Настройки приложения успешно сохранены!')
        return redirect('users:admin_application_settings')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = self.get_object()
        return context


class AdminResetApplicationSettingsView(AdminRequiredMixin, UpdateView):
    """
    Сброс настроек приложения к значениям по умолчанию
    """
    model = ApplicationSettings
    fields = []
    template_name = 'users/admin/application_settings_reset.html'
    
    def get_object(self):
        return ApplicationSettings.get_settings()
    
    def post(self, request, *args, **kwargs):
        settings = self.get_object()
        
        # Сбрасываем настройки к значениям по умолчанию
        settings.app_name = 'Document analyzer'
        settings.app_description = 'Система анализа документов'
        settings.max_file_size = 10485760
        settings.allowed_file_types = 'docx,pdf'
        settings.auto_analysis_enabled = True
        settings.analysis_timeout = 300
        settings.auto_reports_enabled = True
        settings.default_report_format = 'pdf'
        settings.email_notifications_enabled = True
        settings.notification_email = ''
        settings.session_timeout = 3600
        settings.max_login_attempts = 5
        settings.updated_by = request.user
        settings.save()
        
        messages.success(request, 'Настройки приложения сброшены к значениям по умолчанию!')
        return redirect('users:admin_application_settings')


class AdminBulkDeleteDocumentsView(AdminRequiredMixin, View):
    """
    Массовое удаление всех документов для администратора
    """
    
    def get(self, request):
        """Показывает страницу подтверждения"""
        return render(request, 'users/admin/bulk_delete_documents.html', {
            'total_documents': Document.objects.count(),
            'total_comparisons': Comparison.objects.count(),
            'total_reports': Report.objects.count(),
        })
    
    def post(self, request):
        """Выполняет массовое удаление"""
        try:
            # Получаем количество документов до удаления
            documents_count = Document.objects.count()
            comparisons_count = Comparison.objects.count()
            reports_count = Report.objects.count()
            
            # Удаляем все отчеты (они связаны с документами)
            deleted_reports = reports_count
            Report.objects.all().delete()
            
            # Удаляем все сравнения (они связаны с документами)
            deleted_comparisons = comparisons_count
            Comparison.objects.all().delete()
            
            # Удаляем все документы
            deleted_documents = documents_count
            Document.objects.all().delete()
            
            messages.success(request, 
                f'Массовое удаление выполнено успешно! '
                f'Удалено: {deleted_documents} документов, {deleted_comparisons} сравнений, {deleted_reports} отчетов.')
            
            logger.info(f"Admin {request.user.username} performed bulk delete: {deleted_documents} documents, {deleted_comparisons} comparisons, {deleted_reports} reports")
            
        except Exception as e:
            messages.error(request, f'Ошибка при массовом удалении: {str(e)}')
            logger.error(f"Error in bulk delete by admin {request.user.username}: {str(e)}")
        
        return redirect('users:admin_list')


class AdminServerSettingsView(AdminRequiredMixin, CreateView):
    """
    Настройки сервера для администратора
    """
    model = ServerSettings
    form_class = ServerSettingsForm
    template_name = 'users/admin/server_settings.html'
    
    def get_object(self):
        return ServerSettings.get_settings()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.get_object()
        return kwargs
    
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        form.save()
        messages.success(self.request, 'Настройки сервера успешно сохранены!')
        return redirect('users:admin_server_settings')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['settings'] = self.get_object()
        context['system_info'] = get_system_info()
        return context


class AdminServerHealthView(AdminRequiredMixin, ListView):
    """
    Состояние сервера для администратора
    """
    template_name = 'users/admin/server_health.html'
    context_object_name = 'health_data'
    
    def get_queryset(self):
        return [get_server_health()]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['health_data'] = get_server_health()
        context['system_info'] = get_system_info()
        return context


class AdminServerMetricsView(AdminRequiredMixin, ListView):
    """
    Метрики сервера для администратора
    """
    template_name = 'users/admin/server_metrics.html'
    context_object_name = 'metrics_data'
    
    def get_queryset(self):
        return [get_server_metrics()]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['metrics_data'] = get_server_metrics()
        context['system_info'] = get_system_info()
        return context


class AdminResetServerSettingsView(AdminRequiredMixin, UpdateView):
    """
    Сброс настроек сервера к значениям по умолчанию
    """
    model = ServerSettings
    fields = []
    
    def get_object(self):
        return ServerSettings.get_settings()
    
    def get(self, request, *args, **kwargs):
        # Показываем страницу подтверждения
        context = {
            'settings': self.get_object(),
            'title': 'Сброс настроек сервера',
        }
        return render(request, 'users/admin/server_settings_reset.html', context)
    
    def post(self, request, *args, **kwargs):
        settings = self.get_object()
        
        # Сброс к значениям по умолчанию
        settings.server_name = 'Document analyzer Server'
        settings.server_description = 'Сервер системы анализа документов Document analyzer'
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
        logger.info(f"Admin {request.user.username} reset server settings to defaults")
        
        return redirect('users:admin_server_settings')
