from django.urls import path
from . import views, admin_views

app_name = 'users'

urlpatterns = [
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.CustomLogoutView.as_view(), name='logout'),
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('register/', views.UserRegisterView.as_view(), name='register'),
    
    # Админ-функции для управления пользователями
    path('admin/', admin_views.AdminUserListView.as_view(), name='admin_list'),
    path('admin/create/', admin_views.AdminUserCreateView.as_view(), name='admin_create'),
    path('admin/<int:pk>/', admin_views.AdminUserDetailView.as_view(), name='admin_detail'),
    path('admin/<int:pk>/edit/', admin_views.AdminUserEditView.as_view(), name='admin_edit'),
    path('admin/<int:pk>/delete/', admin_views.AdminUserDeleteView.as_view(), name='admin_delete'),
    path('admin/<int:pk>/toggle-active/', admin_views.AdminUserToggleActiveView.as_view(), name='admin_toggle_active'),
    
    # Настройки приложения
    path('admin/application-settings/', admin_views.AdminApplicationSettingsView.as_view(), name='admin_application_settings'),
    path('admin/application-settings/reset/', admin_views.AdminResetApplicationSettingsView.as_view(), name='admin_application_settings_reset'),
    
    # Массовое удаление
    path('admin/bulk-delete-documents/', admin_views.AdminBulkDeleteDocumentsView.as_view(), name='admin_bulk_delete_documents'),
    
    # Настройки сервера
    path('admin/server-settings/', admin_views.AdminServerSettingsView.as_view(), name='admin_server_settings'),
    path('admin/server-settings/reset/', admin_views.AdminResetServerSettingsView.as_view(), name='admin_server_settings_reset'),
    path('admin/server-health/', admin_views.AdminServerHealthView.as_view(), name='admin_server_health'),
    path('admin/server-metrics/', admin_views.AdminServerMetricsView.as_view(), name='admin_server_metrics'),
]
