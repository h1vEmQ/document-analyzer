# Импортируем версию приложения
from .version import __version__, __year__, __app_name__, __copyright__

# Это обеспечит загрузку приложения Celery при запуске Django (опционально)
try:
    from .celery import app as celery_app
    __all__ = ('celery_app', '__version__', '__year__', '__app_name__', '__copyright__')
except ImportError:
    # Celery не установлен, продолжаем без него
    __all__ = ('__version__', '__year__', '__app_name__', '__copyright__')

