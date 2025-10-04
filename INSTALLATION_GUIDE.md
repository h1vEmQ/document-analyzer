# 📋 Инструкция по установке и настройке Document analyzer

## 🎯 Обзор
**Document analyzer** - это система анализа документов с поддержкой AI-анализа через Ollama и асинхронной обработки через Celery.

---

## 📋 Системные требования

### Минимальные требования:
- **OS**: macOS 10.15+, Ubuntu 18.04+, Windows 10+
- **Python**: 3.8+ (рекомендуется 3.13)
- **RAM**: 4 GB (рекомендуется 8 GB)
- **Диск**: 2 GB свободного места
- **Сеть**: Интернет для загрузки зависимостей

### Дополнительные компоненты:
- **Redis**: для Celery (асинхронная обработка)
- **Ollama**: для AI-анализа (опционально)

---

## 🚀 Быстрая установка

### 1. Клонирование проекта
```bash
git clone <repository-url>
cd WARA
```

### 2. Создание виртуального окружения
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Создание суперпользователя
```bash
python manage.py createsuperuser
```

### 6. Запуск сервера
```bash
python manage.py runserver
```

**Готово!** Сервер доступен по адресу: http://localhost:8000

---

## ⚙️ Подробная настройка

### 1. Настройка Redis (для Celery)

#### macOS (с Homebrew):
```bash
brew install redis
brew services start redis
```

#### Ubuntu/Debian:
```bash
sudo apt update
sudo apt install redis-server
sudo systemctl start redis
sudo systemctl enable redis
```

#### Windows:
1. Скачать Redis с https://github.com/tporadowski/redis/releases
2. Запустить `redis-server.exe`

#### Проверка работы Redis:
```bash
redis-cli ping
# Должен вернуть: PONG
```

### 2. Настройка Ollama (опционально)

#### Установка Ollama:
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Windows
# Скачать с https://ollama.ai/download
```

#### Запуск Ollama:
```bash
ollama serve
```

#### Загрузка модели:
```bash
ollama pull llama3
ollama pull codellama
```

#### Проверка работы:
```bash
curl http://localhost:11434/api/tags
```

### 3. Настройка Celery Worker

#### Запуск в отдельном терминале:
```bash
# Активировать виртуальное окружение
source venv/bin/activate

# Запустить Celery worker
celery -A wara_project worker -l info
```

#### Или использовать скрипт:
```bash
chmod +x start_celery_worker.sh
./start_celery_worker.sh
```

---

## 🔧 Конфигурация

### 1. Настройки Django (`wara_project/settings.py`)

#### Основные настройки:
```python
# База данных
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'

# Медиа файлы
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
```

### 2. Настройки приложения (через веб-интерфейс)

1. Войти в систему как суперпользователь
2. Перейти в админ-панель: `/users/admin/`
3. Настроить параметры:
   - **Название приложения**: Document analyzer
   - **Максимальный размер файла**: 10 MB
   - **Разрешенные типы**: docx,pdf
   - **Формат отчетов по умолчанию**: PDF или DOCX

### 3. Настройки сервера

В админ-панели `/users/admin/server-settings/`:
- **Максимальные одновременные запросы**: 100
- **Таймаут запроса**: 30 секунд
- **Максимальное использование памяти**: 2048 MB
- **Уровень логирования**: INFO

---

## 📁 Структура проекта

```
WARA/
├── analysis/              # Модуль анализа документов
├── documents/             # Модуль управления документами
├── reports/               # Модуль генерации отчетов
├── users/                 # Модуль пользователей
├── settings/              # Модуль настроек
├── templates/             # HTML шаблоны
├── media/                 # Загруженные файлы
│   ├── documents/         # Документы
│   └── reports/           # Сгенерированные отчеты
├── wara_project/          # Настройки Django
├── requirements.txt       # Зависимости Python
├── manage.py             # Управление Django
└── db.sqlite3            # База данных SQLite
```

---

## 🔍 Проверка установки

### 1. Проверка основных компонентов

#### Django сервер:
```bash
curl http://localhost:8000
# Должен вернуть HTML страницу
```

#### Redis:
```bash
redis-cli ping
# Должен вернуть: PONG
```

#### Celery:
```bash
celery -A wara_project inspect active
# Должен показать активные задачи
```

#### Ollama (если установлен):
```bash
curl http://localhost:11434/api/tags
# Должен вернуть список моделей
```

### 2. Функциональное тестирование

1. **Загрузка документа**:
   - Перейти на http://localhost:8000/documents/upload/
   - Загрузить DOCX файл
   - Проверить, что документ появился в списке

2. **Создание анализа**:
   - Перейти на http://localhost:8000/analysis/create/
   - Выбрать два документа
   - Создать сравнение
   - Проверить результат

3. **AI-анализ** (если Ollama установлен):
   - Перейти на http://localhost:8000/analysis/ollama/create/
   - Выбрать модель и документы
   - Запустить анализ
   - Проверить результат

4. **Генерация отчета**:
   - Перейти на http://localhost:8000/reports/
   - Создать отчет для анализа
   - Скачать PDF/DOCX файл

---

## 🚨 Устранение неполадок

### Проблема: "Port already in use"
```bash
# Найти процесс
ps aux | grep runserver

# Завершить процесс
kill -9 <PID>

# Или использовать другой порт
python manage.py runserver 8001
```

### Проблема: "ModuleNotFoundError: No module named 'celery'"
```bash
# Переустановить зависимости
pip install -r requirements.txt

# Проверить виртуальное окружение
which python
```

### Проблема: "Redis connection refused"
```bash
# Запустить Redis
brew services start redis  # macOS
sudo systemctl start redis  # Linux

# Проверить порт
netstat -an | grep 6379
```

### Проблема: "Ollama service unavailable"
```bash
# Запустить Ollama
ollama serve

# Проверить доступность
curl http://localhost:11434/api/tags
```

### Проблема: "Permission denied" при загрузке файлов
```bash
# Установить права на media папку
chmod -R 755 media/
chown -R www-data:www-data media/  # Linux
```

---

## 📊 Мониторинг и логи

### Логи Django:
```bash
# Просмотр логов в реальном времени
tail -f logs/django.log

# Или через manage.py
python manage.py runserver --verbosity=2
```

### Логи Celery:
```bash
# Логи worker'а
celery -A wara_project worker -l debug

# Статус задач
celery -A wara_project inspect active
celery -A wara_project inspect scheduled
```

### Мониторинг Redis:
```bash
# Подключение к Redis CLI
redis-cli

# Информация о памяти
INFO memory

# Список ключей
KEYS *
```

---

## 🔄 Обновление системы

### 1. Обновление кода:
```bash
git pull origin main
```

### 2. Обновление зависимостей:
```bash
pip install -r requirements.txt --upgrade
```

### 3. Применение миграций:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Перезапуск сервисов:
```bash
# Остановить сервер
Ctrl+C

# Перезапустить сервер
python manage.py runserver

# Перезапустить Celery worker
celery -A wara_project worker -l info
```

---

## 🚀 Развертывание в продакшене

### 1. Использование PostgreSQL:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'document_analyzer',
        'USER': 'your_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### 2. Настройка статических файлов:
```python
# settings.py
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 3. Использование Gunicorn:
```bash
pip install gunicorn
gunicorn wara_project.wsgi:application --bind 0.0.0.0:8000
```

### 4. Настройка Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /media/ {
        alias /path/to/WARA/media/;
    }
    
    location /static/ {
        alias /path/to/WARA/staticfiles/;
    }
}
```

---

## 📞 Поддержка

### Полезные команды:
```bash
# Проверка статуса всех сервисов
python manage.py check

# Создание резервной копии БД
python manage.py dumpdata > backup.json

# Восстановление из резервной копии
python manage.py loaddata backup.json

# Очистка старых файлов
python manage.py clearsessions
```

### Контакты:
- **Команда разработки**: Document analyzer Development Team
- **Email**: contact@document-analyzer.com
- **Версия**: 1.0.0
- **Дата**: 2025

---

## ✅ Чек-лист установки

- [ ] Python 3.8+ установлен
- [ ] Виртуальное окружение создано и активировано
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] База данных настроена (`python manage.py migrate`)
- [ ] Суперпользователь создан (`python manage.py createsuperuser`)
- [ ] Django сервер запущен (`python manage.py runserver`)
- [ ] Redis установлен и запущен
- [ ] Celery worker запущен
- [ ] Ollama установлен и запущен (опционально)
- [ ] Тестовый документ загружен
- [ ] Анализ создан и протестирован
- [ ] Отчет сгенерирован и скачан

**🎉 Поздравляем! Document analyzer успешно установлен и настроен!**
