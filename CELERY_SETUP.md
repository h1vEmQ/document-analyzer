# Настройка фоновых задач для анализа нейросетью

## Обзор

Система теперь использует Celery для выполнения анализа нейросетью в фоновом режиме, что улучшает пользовательский опыт и предотвращает зависание интерфейса.

## Требования

1. **Redis** - брокер сообщений для Celery
2. **Celery** - система фоновых задач
3. **Celery Worker** - процесс, выполняющий задачи

## Установка зависимостей

```bash
# Установка Python зависимостей
pip install -r requirements.txt

# Установка Redis (Ubuntu/Debian)
sudo apt update
sudo apt install redis-server

# Установка Redis (macOS)
brew install redis

# Установка Redis (Windows)
# Скачайте Redis с https://github.com/microsoftarchive/redis/releases
```

## Запуск системы

### 1. Запуск Redis

```bash
# Ubuntu/Debian
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS
brew services start redis

# Windows
# Запустите redis-server.exe из папки установки
```

### 2. Запуск Django сервера

```bash
source venv/bin/activate
python manage.py runserver
```

### 3. Запуск Celery Worker

В отдельном терминале:

```bash
# Используя скрипт
./start_celery_worker.sh

# Или вручную
source venv/bin/activate
celery -A wara_project worker --loglevel=info --concurrency=1
```

## Проверка работы

1. Откройте веб-интерфейс
2. Перейдите в раздел "Анализ" → "Анализ нейросетью"
3. Создайте новый анализ
4. Вы должны увидеть сообщение о том, что анализ запущен в фоновом режиме
5. Страница будет автоматически обновляться каждые 10 секунд

## Мониторинг

### Проверка статуса Celery

```bash
# В отдельном терминале
source venv/bin/activate
celery -A wara_project inspect active
celery -A wara_project inspect stats
```

### Проверка Redis

```bash
# Подключение к Redis CLI
redis-cli ping
# Должно вернуть: PONG
```

## Структура фоновых задач

### Основная задача: `run_ollama_analysis`

- **Входные параметры**: `comparison_id`, `user_id`
- **Статусы анализа**:
  - `pending` - ожидает обработки
  - `processing` - выполняется
  - `completed` - завершен
  - `error` - ошибка

### Автоматические действия

1. При запуске анализа создается запись со статусом `pending`
2. Celery worker получает задачу и меняет статус на `processing`
3. Выполняется анализ с помощью Ollama
4. Результат сохраняется, статус меняется на `completed`
5. Автоматически создается отчет в формате из настроек
6. Веб-интерфейс обновляется и показывает результаты

## Устранение неполадок

### Redis не запущен
```
Error: [Errno 111] Connection refused
```
**Решение**: Запустите Redis сервер

### Celery worker не работает
```
No module named 'celery'
```
**Решение**: Установите зависимости `pip install -r requirements.txt`

### Задачи не выполняются
1. Проверьте, что Redis запущен
2. Проверьте, что Celery worker запущен
3. Проверьте логи Celery worker

### Анализ зависает
1. Проверьте, что Ollama запущен на localhost:11434
2. Проверьте логи Celery worker для ошибок
3. Убедитесь, что документы содержат текст

## Производительность

- **Concurrency**: 1 (настройте под ваши ресурсы)
- **Timeout**: 30 минут на задачу
- **Retry**: Автоматические повторы при ошибках
- **Memory**: Задачи выполняются в отдельных процессах

## Безопасность

- Задачи выполняются с правами пользователя Django
- Входные данные валидируются перед выполнением
- Результаты сохраняются в базе данных
- Логирование всех операций
