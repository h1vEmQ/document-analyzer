"""
Сервис для работы с Microsoft Graph API
"""
import logging
import msal
from msal import ConfidentialClientApplication
from typing import Optional, Dict, List, Any
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import requests
import io
import json

logger = logging.getLogger(__name__)


class MicrosoftGraphService:
    """Сервис для работы с Microsoft Graph API"""
    
    def __init__(self):
        """Инициализация сервиса"""
        self._app = None
        self._graph_client = None
        self._settings = None
    
    @property
    def app_settings(self):
        """Получить настройки Microsoft Graph"""
        if not self._settings:
            from .models import ApplicationSettings
            self._settings = ApplicationSettings.get_settings()
        return self._settings
    
    @property
    def is_enabled(self):
        """Проверить, включена ли интеграция с Microsoft Graph"""
        return self.app_settings.microsoft_graph_enabled
    
    @property
    def app(self):
        """Получить экземпляр MSAL приложения"""
        if not self._app and self.is_enabled:
            settings = self.app_settings
            
            if not all([
                settings.microsoft_tenant_id,
                settings.microsoft_client_id,
                settings.microsoft_client_secret
            ]):
                raise ValueError("Не все настройки Microsoft Graph заполнены")
            
            self._app = ConfidentialClientApplication(
                client_id=settings.microsoft_client_id,
                client_credential=settings.microsoft_client_secret,
                authority=f"https://login.microsoftonline.com/{settings.microsoft_tenant_id}"
            )
        
        return self._app
    
    def get_auth_url(self, user_id: str) -> str:
        """Получить URL для авторизации пользователя"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        settings = self.app_settings
        scopes = settings.microsoft_scope.split()
        
        # Создаем state для сохранения user_id
        state = json.dumps({"user_id": user_id})
        
        auth_url = self.app.get_authorization_request_url(
            scopes=scopes,
            redirect_uri=settings.microsoft_redirect_uri,
            state=state
        )
        
        return auth_url
    
    def get_token_from_code(self, code: str, user_id: str) -> Dict[str, Any]:
        """Получить токен доступа по коду авторизации"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        settings = self.app_settings
        scopes = settings.microsoft_scope.split()
        
        result = self.app.acquire_token_by_authorization_code(
            code=code,
            scopes=scopes,
            redirect_uri=settings.microsoft_redirect_uri
        )
        
        if "error" in result:
            raise ValueError(f"Ошибка получения токена: {result.get('error_description', result['error'])}")
        
        # Сохраняем токен в базе данных
        self._save_token(user_id, result)
        
        return result
    
    def _save_token(self, user_id: str, token_result: Dict[str, Any]):
        """Сохранить токен в базе данных"""
        from django.contrib.auth import get_user_model
        from .models import MicrosoftGraphToken
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Вычисляем время истечения токена
        expires_in = token_result.get('expires_in', 3600)
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        # Создаем или обновляем токен
        token_obj, created = MicrosoftGraphToken.objects.update_or_create(
            user=user,
            defaults={
                'access_token': token_result['access_token'],
                'refresh_token': token_result.get('refresh_token', ''),
                'token_type': token_result.get('token_type', 'Bearer'),
                'expires_at': expires_at,
                'scope': ' '.join(token_result.get('scope', []))
            }
        )
        
        logger.info(f"Токен Microsoft Graph {'создан' if created else 'обновлен'} для пользователя {user.username}")
    
    def get_valid_token(self, user_id: str) -> Optional[str]:
        """Получить валидный токен доступа для пользователя"""
        from django.contrib.auth import get_user_model
        from .models import MicrosoftGraphToken
        
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        try:
            token_obj = MicrosoftGraphToken.objects.get(user=user)
            
            # Проверяем, не истек ли токен
            if token_obj.is_expired:
                # Пытаемся обновить токен
                if token_obj.refresh_token:
                    self._refresh_token(token_obj)
                else:
                    return None
            
            return token_obj.access_token
            
        except MicrosoftGraphToken.DoesNotExist:
            return None
    
    def _refresh_token(self, token_obj):
        """Обновить токен доступа"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        settings = self.app_settings
        scopes = settings.microsoft_scope.split()
        
        result = self.app.acquire_token_by_refresh_token(
            refresh_token=token_obj.refresh_token,
            scopes=scopes
        )
        
        if "error" in result:
            logger.error(f"Ошибка обновления токена: {result.get('error_description', result['error'])}")
            return None
        
        # Обновляем токен в базе данных
        expires_in = result.get('expires_in', 3600)
        expires_at = timezone.now() + timedelta(seconds=expires_in)
        
        token_obj.access_token = result['access_token']
        token_obj.refresh_token = result.get('refresh_token', token_obj.refresh_token)
        token_obj.expires_at = expires_at
        token_obj.scope = ' '.join(result.get('scope', []))
        token_obj.save()
        
        logger.info(f"Токен обновлен для пользователя {token_obj.user.username}")
    
    def get_graph_client(self, user_id: str) -> str:
        """Получить токен для Microsoft Graph API"""
        token = self.get_valid_token(user_id)
        if not token:
            raise ValueError("Не удалось получить валидный токен доступа")
        
        return token
    
    def list_documents(self, user_id: str, folder_path: Optional[str] = None) -> List[Dict[str, Any]]:
        """Получить список документов из SharePoint"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        try:
            token = self.get_graph_client(user_id)
            app_settings = self.app_settings
            
            # Определяем путь к папке
            if folder_path is None:
                folder_path = app_settings.microsoft_folder_path or '/Documents'
            
            # Формируем URL для запроса
            if app_settings.microsoft_site_id and app_settings.microsoft_drive_id:
                # Используем конкретный сайт и диск
                site_parts = app_settings.microsoft_site_id.split(',')
                if len(site_parts) >= 3:
                    site_hostname, site_id, web_id = site_parts[0], site_parts[1], site_parts[2]
                    graph_url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:/sites/{site_id}:/drive/root:{folder_path}:/children"
                else:
                    graph_url = f"https://graph.microsoft.com/v1.0/drives/{app_settings.microsoft_drive_id}/root:{folder_path}/children"
            else:
                # Используем основной диск пользователя
                graph_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}/children"
            
            # Выполняем запрос к Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(graph_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            if 'value' in data:
                documents = []
                for item in data['value']:
                    if 'file' in item:
                        documents.append({
                            'id': item['id'],
                            'name': item['name'],
                            'size': item.get('size', 0),
                            'last_modified': item.get('lastModifiedDateTime', ''),
                            'download_url': item.get('@microsoft.graph.downloadUrl', ''),
                            'web_url': item.get('webUrl', '')
                        })
                
                return documents
            
            return []
            
        except Exception as e:
            logger.error(f"Ошибка получения списка документов: {str(e)}")
            raise
    
    def download_document(self, user_id: str, document_id: str) -> bytes:
        """Скачать документ по ID"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        try:
            token = self.get_graph_client(user_id)
            app_settings = self.app_settings
            
            # Формируем URL для скачивания
            if app_settings.microsoft_site_id and app_settings.microsoft_drive_id:
                # Используем конкретный сайт и диск
                site_parts = app_settings.microsoft_site_id.split(',')
                if len(site_parts) >= 3:
                    site_hostname, site_id, web_id = site_parts[0], site_parts[1], site_parts[2]
                    download_url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:/sites/{site_id}:/drive/items/{document_id}/content"
                else:
                    download_url = f"https://graph.microsoft.com/v1.0/drives/{app_settings.microsoft_drive_id}/items/{document_id}/content"
            else:
                # Используем основной диск пользователя
                download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{document_id}/content"
            
            # Выполняем запрос к Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.get(download_url, headers=headers)
            response.raise_for_status()
            
            return response.content
            
        except Exception as e:
            logger.error(f"Ошибка скачивания документа {document_id}: {str(e)}")
            raise
    
    def upload_document(self, user_id: str, file_content: bytes, file_name: str, folder_path: Optional[str] = None) -> Dict[str, Any]:
        """Загрузить документ в SharePoint"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        try:
            token = self.get_graph_client(user_id)
            app_settings = self.app_settings
            
            # Определяем путь к папке
            if folder_path is None:
                folder_path = app_settings.microsoft_folder_path or '/Documents'
            
            # Формируем URL для загрузки
            if app_settings.microsoft_site_id and app_settings.microsoft_drive_id:
                # Используем конкретный сайт и диск
                site_parts = app_settings.microsoft_site_id.split(',')
                if len(site_parts) >= 3:
                    site_hostname, site_id, web_id = site_parts[0], site_parts[1], site_parts[2]
                    upload_url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:/sites/{site_id}:/drive/root:{folder_path}:/{file_name}:/content"
                else:
                    upload_url = f"https://graph.microsoft.com/v1.0/drives/{app_settings.microsoft_drive_id}/root:{folder_path}/{file_name}/content"
            else:
                # Используем основной диск пользователя
                upload_url = f"https://graph.microsoft.com/v1.0/me/drive/root:{folder_path}/{file_name}/content"
            
            # Выполняем запрос к Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream'
            }
            
            response = requests.put(upload_url, data=file_content, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            return {
                'id': data['id'],
                'name': data['name'],
                'size': data.get('size', 0),
                'web_url': data.get('webUrl', ''),
                'download_url': data.get('@microsoft.graph.downloadUrl', '')
            }
            
        except Exception as e:
            logger.error(f"Ошибка загрузки документа {file_name}: {str(e)}")
            raise
    
    def delete_document(self, user_id: str, document_id: str) -> bool:
        """Удалить документ по ID"""
        if not self.is_enabled:
            raise ValueError("Интеграция с Microsoft Graph не включена")
        
        try:
            token = self.get_graph_client(user_id)
            app_settings = self.app_settings
            
            # Формируем URL для удаления
            if app_settings.microsoft_site_id and app_settings.microsoft_drive_id:
                # Используем конкретный сайт и диск
                site_parts = app_settings.microsoft_site_id.split(',')
                if len(site_parts) >= 3:
                    site_hostname, site_id, web_id = site_parts[0], site_parts[1], site_parts[2]
                    delete_url = f"https://graph.microsoft.com/v1.0/sites/{site_hostname}:/sites/{site_id}:/drive/items/{document_id}"
                else:
                    delete_url = f"https://graph.microsoft.com/v1.0/drives/{app_settings.microsoft_drive_id}/items/{document_id}"
            else:
                # Используем основной диск пользователя
                delete_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{document_id}"
            
            # Выполняем запрос к Microsoft Graph API
            headers = {
                'Authorization': f'Bearer {token}'
            }
            
            response = requests.delete(delete_url, headers=headers)
            response.raise_for_status()
            
            logger.info(f"Документ {document_id} успешно удален")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка удаления документа {document_id}: {str(e)}")
            raise
    
    def test_connection(self, user_id: str) -> Dict[str, Any]:
        """Тестировать соединение с Microsoft Graph"""
        if not self.is_enabled:
            return {
                'success': False,
                'error': 'Интеграция с Microsoft Graph не включена'
            }
        
        try:
            # Проверяем наличие токена
            token = self.get_valid_token(user_id)
            if not token:
                return {
                    'success': False,
                    'error': 'Не удалось получить валидный токен доступа'
                }
            
            # Пытаемся получить информацию о пользователе
            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get('https://graph.microsoft.com/v1.0/me', headers=headers)
            response.raise_for_status()
            
            user_data = response.json()
            
            return {
                'success': True,
                'user': {
                    'id': user_data.get('id', ''),
                    'display_name': user_data.get('displayName', ''),
                    'mail': user_data.get('mail', ''),
                    'user_principal_name': user_data.get('userPrincipalName', '')
                }
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Ошибка соединения: {str(e)}'
            }
