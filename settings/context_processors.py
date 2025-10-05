from .models import ApplicationSettings


def app_settings(request):
    """
    Контекстный процессор для добавления настроек приложения во все шаблоны
    """
    try:
        settings = ApplicationSettings.get_settings()
        return {
            'app_name': settings.app_name,
            'app_description': settings.app_description,
        }
    except Exception:
        # В случае ошибки возвращаем значения по умолчанию
        return {
            'app_name': '📊 Анализатор документов',
            'app_description': 'Система анализа документов',
        }
