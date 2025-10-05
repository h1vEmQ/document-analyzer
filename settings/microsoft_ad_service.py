"""
Сервис для авторизации через Microsoft Active Directory SSO
"""
import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User
from msal import ConfidentialClientApplication, PublicClientApplication
import json
import uuid
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

User = get_user_model()


class MicrosoftADAuthService:
    """Сервис для авторизации через Microsoft Active Directory"""
    
    def __init__(self):
        from .models import ApplicationSettings
        self.settings = ApplicationSettings.get_settings()
        
        if not self.settings.microsoft_ad_sso_enabled:
            raise ValueError("Microsoft AD SSO не включен в настройках")
        
        self.tenant_id = self.settings.microsoft_ad_sso_tenant_id
        self.client_id = self.settings.microsoft_ad_sso_client_id
        self.client_secret = self.settings.microsoft_ad_sso_client_secret
        self.redirect_uri = self.settings.microsoft_ad_sso_redirect_uri
        self.scope = self.settings.microsoft_ad_sso_scope.split()
        self.domain = self.settings.microsoft_ad_sso_domain
        
        # Создаем MSAL приложение
        self.msal_app = ConfidentialClientApplication(
            client_id=self.client_id,
            client_credential=self.client_secret,
            authority=f"https://login.microsoftonline.com/{self.tenant_id}"
        )
    
    def get_auth_url(self, state=None):
        """Получить URL для авторизации"""
        if not state:
            state = str(uuid.uuid4())
        
        try:
            auth_url = self.msal_app.get_authorization_request_url(
                scopes=self.scope,
                redirect_uri=self.redirect_uri,
                state=state
            )
            return auth_url, state
        except Exception as e:
            logger.error(f"Ошибка создания URL авторизации: {e}")
            raise
    
    def get_token_from_code(self, code, state=None):
        """Получить токен доступа по коду авторизации"""
        try:
            result = self.msal_app.acquire_token_by_authorization_code(
                code=code,
                scopes=self.scope,
                redirect_uri=self.redirect_uri
            )
            
            if "error" in result:
                logger.error(f"Ошибка получения токена: {result['error']}")
                raise Exception(f"Ошибка авторизации: {result['error']}")
            
            return result
        except Exception as e:
            logger.error(f"Ошибка получения токена: {e}")
            raise
    
    def get_user_info(self, access_token):
        """Получить информацию о пользователе"""
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка получения информации о пользователе: {response.status_code}")
                raise Exception(f"Не удалось получить информацию о пользователе: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Ошибка запроса информации о пользователе: {e}")
            raise
    
    def validate_user_domain(self, email):
        """Проверить, что пользователь принадлежит к нужному домену"""
        if not self.domain:
            return True
        
        if not email or '@' not in email:
            return False
        
        user_domain = email.split('@')[1].lower()
        return user_domain == self.domain.lower()
    
    def create_or_update_user(self, user_info):
        """Создать или обновить пользователя в системе"""
        try:
            email = user_info.get('mail') or user_info.get('userPrincipalName')
            if not email:
                raise ValueError("Email пользователя не найден")
            
            # Проверяем домен
            if not self.validate_user_domain(email):
                raise ValueError(f"Пользователь не принадлежит к домену {self.domain}")
            
            # Ищем существующего пользователя
            try:
                user = User.objects.get(email=email)
                # Обновляем информацию
                user.first_name = user_info.get('givenName', '')
                user.last_name = user_info.get('surname', '')
                user.save()
            except User.DoesNotExist:
                # Создаем нового пользователя
                username = user_info.get('userPrincipalName', email)
                # Убираем домен из username если есть
                if '@' in username:
                    username = username.split('@')[0]
                
                # Проверяем уникальность username
                original_username = username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{original_username}{counter}"
                    counter += 1
                
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    first_name=user_info.get('givenName', ''),
                    last_name=user_info.get('surname', ''),
                    is_active=True
                )
                
                logger.info(f"Создан новый пользователь AD SSO: {username} ({email})")
            
            return user
            
        except Exception as e:
            logger.error(f"Ошибка создания/обновления пользователя: {e}")
            raise
    
    def test_connection(self):
        """Тестировать соединение с Microsoft Graph"""
        try:
            # Пробуем создать приложение MSAL
            app = ConfidentialClientApplication(
                client_id=self.client_id,
                client_credential=self.client_secret,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}"
            )
            
            # Пробуем получить URL авторизации
            auth_url, _ = self.get_auth_url()
            
            return True, "Соединение успешно"
            
        except Exception as e:
            logger.error(f"Ошибка тестирования соединения: {e}")
            return False, str(e)


class MicrosoftADAuthBackend(BaseBackend):
    """Django authentication backend для Microsoft AD SSO"""
    
    def authenticate(self, request, **kwargs):
        """Аутентификация через Microsoft AD SSO"""
        if not request:
            return None
        
        # Проверяем, что AD SSO включен
        from .models import ApplicationSettings
        settings_obj = ApplicationSettings.get_settings()
        if not settings_obj.microsoft_ad_sso_enabled:
            return None
        
        # Получаем токен из сессии
        access_token = request.session.get('microsoft_ad_access_token')
        if not access_token:
            return None
        
        try:
            # Создаем сервис
            ad_service = MicrosoftADAuthService()
            
            # Получаем информацию о пользователе
            user_info = ad_service.get_user_info(access_token)
            
            # Создаем или обновляем пользователя
            user = ad_service.create_or_update_user(user_info)
            
            return user
            
        except Exception as e:
            logger.error(f"Ошибка аутентификации AD SSO: {e}")
            return None
    
    def get_user(self, user_id):
        """Получить пользователя по ID"""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
