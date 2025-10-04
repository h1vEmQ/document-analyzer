from django.apps import AppConfig


class SettingsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'settings'
    verbose_name = 'Настройки приложения'
    
    def ready(self):
        """Инициализация приложения"""
        # Импортируем сигналы, если они есть
        try:
            import settings.signals
        except ImportError:
            pass