from django.urls import path
from . import views

app_name = 'settings'

urlpatterns = [
    path('', views.settings_view, name='settings'),
    path('reset/', views.reset_settings, name='reset'),
    path('quick/', views.quick_settings_view, name='quick'),
    path('api/', views.settings_api, name='api'),
    path('api/update/', views.SettingsAPIView.as_view(), name='api_update'),
    path('export/', views.settings_export, name='export'),
    path('import/', views.settings_import, name='import'),
]
