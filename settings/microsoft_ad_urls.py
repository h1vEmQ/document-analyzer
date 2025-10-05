"""
URL маршруты для Microsoft Active Directory SSO
"""
from django.urls import path
from . import microsoft_ad_views

app_name = 'microsoft_ad'

urlpatterns = [
    # Основные маршруты авторизации
    path('login/', microsoft_ad_views.microsoft_ad_login, name='login'),
    path('callback/', microsoft_ad_views.microsoft_ad_callback, name='callback'),
    path('logout/', microsoft_ad_views.microsoft_ad_logout, name='logout'),
    path('login-page/', microsoft_ad_views.microsoft_ad_login_page, name='login_page'),
    
    # Утилиты
    path('status/', microsoft_ad_views.microsoft_ad_status, name='status'),
    path('test/', microsoft_ad_views.microsoft_ad_test, name='test'),
    path('disable/', microsoft_ad_views.microsoft_ad_disable, name='disable'),
]
