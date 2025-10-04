#!/bin/bash
# Скрипт для запуска Celery worker

echo "Запуск Celery worker для Document analyzer..."

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем Celery worker
celery -A wara_project worker --loglevel=info --concurrency=1

echo "Celery worker остановлен"
