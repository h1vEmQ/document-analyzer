"""
URL-маршруты для Microsoft Graph API
"""
from django.urls import path
from . import microsoft_views

app_name = 'microsoft'

urlpatterns = [
    # Авторизация
    path('auth/start/', microsoft_views.microsoft_auth_start, name='auth_start'),
    path('auth/callback/', microsoft_views.microsoft_auth_callback, name='auth_callback'),
    path('auth/status/', microsoft_views.microsoft_auth_status, name='auth_status'),
    path('auth/disconnect/', microsoft_views.microsoft_disconnect, name='disconnect'),
    
    # Тестирование
    path('test/', microsoft_views.microsoft_test_connection, name='test'),
    
    # Документы
    path('documents/', microsoft_views.microsoft_documents_list, name='documents_list'),
    path('documents/<str:document_id>/download/', microsoft_views.microsoft_document_download, name='document_download'),
    path('documents/upload/', microsoft_views.microsoft_upload_document, name='document_upload'),
]
