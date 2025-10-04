import os
from celery import Celery

# Устанавливаем переменную окружения Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')

app = Celery('wara_project')

# Используем namespace='CELERY' означает, что все настройки Celery
# должны иметь префикс `CELERY_`.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически обнаруживаем задачи в приложениях Django.
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

