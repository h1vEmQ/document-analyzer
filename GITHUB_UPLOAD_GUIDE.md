# 🚀 Инструкция по загрузке проекта на GitHub

## 📋 Обзор

Данная инструкция поможет вам загрузить проект **📊 Анализатор документов** на GitHub и настроить удаленный репозиторий для совместной работы.

---

## 🔧 Предварительные требования

### 1. Установка Git
```bash
# Проверка установки Git
git --version

# Если Git не установлен:
# macOS (с Homebrew)
brew install git

# Ubuntu/Debian
sudo apt update
sudo apt install git

# Windows
# Скачайте с https://git-scm.com/download/win
```

### 2. Настройка Git (если не настроен)
```bash
# Настройка имени пользователя
git config --global user.name "Ваше Имя"

# Настройка email
git config --global user.email "your.email@example.com"

# Проверка настроек
git config --global --list
```

### 3. Создание аккаунта на GitHub
1. Перейдите на [github.com](https://github.com)
2. Нажмите "Sign up"
3. Заполните форму регистрации
4. Подтвердите email

---

## 🏗️ Создание репозитория на GitHub

### 1. Создание нового репозитория
1. Войдите в свой аккаунт GitHub
2. Нажмите зеленую кнопку **"New"** или **"+"** → **"New repository"**
3. Заполните форму:
   - **Repository name**: `document-analyzer` (или любое другое название)
   - **Description**: `📊 Система анализа документов с поддержкой AI-анализа и асинхронной обработки`
   - **Visibility**: 
     - ✅ **Public** (для открытого проекта)
     - ✅ **Private** (для закрытого проекта)
   - **Initialize repository**:
     - ❌ НЕ ставьте галочку "Add a README file"
     - ❌ НЕ ставьте галочку "Add .gitignore"
     - ❌ НЕ ставьте галочку "Choose a license"
4. Нажмите **"Create repository"**

### 2. Получение URL репозитория
После создания репозитория GitHub покажет инструкции. Скопируйте URL:
- **HTTPS**: `https://github.com/ваш-username/document-analyzer.git`
- **SSH**: `git@github.com:ваш-username/document-analyzer.git`

---

## 📤 Загрузка проекта на GitHub

### 1. Переход в директорию проекта
```bash
cd /Users/wind/Documents/RA
```

### 2. Проверка текущего статуса
```bash
git status
# Должно показать: "working tree clean"
```

### 3. Добавление удаленного репозитория
```bash
# Замените URL на ваш реальный URL репозитория
git remote add origin https://github.com/ваш-username/document-analyzer.git

# Проверка добавленного репозитория
git remote -v
```

### 4. Переименование основной ветки (если нужно)
```bash
# Переименование ветки main (если текущая ветка называется master)
git branch -M main

# Проверка текущей ветки
git branch
```

### 5. Первая загрузка на GitHub
```bash
# Загрузка кода на GitHub
git push -u origin main
```

### 6. Проверка загрузки
1. Обновите страницу репозитория на GitHub
2. Убедитесь, что все файлы загружены
3. Проверьте, что README_FINAL.md отображается как главная страница

---

## 🔐 Настройка аутентификации

### Вариант 1: Personal Access Token (Рекомендуется)
```bash
# Создание токена на GitHub:
# 1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
# 2. Generate new token (classic)
# 3. Выберите scopes: repo, workflow, write:packages
# 4. Скопируйте токен

# При первом push Git попросит ввести:
# Username: ваш-username
# Password: ваш-personal-access-token
```

### Вариант 2: SSH ключи
```bash
# Генерация SSH ключа
ssh-keygen -t ed25519 -C "your.email@example.com"

# Добавление ключа в ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

# Копирование публичного ключа
cat ~/.ssh/id_ed25519.pub

# Добавление ключа на GitHub:
# 1. GitHub → Settings → SSH and GPG keys
# 2. New SSH key
# 3. Вставьте скопированный ключ
```

---

## 📝 Настройка README и описания

### 1. Автоматическое отображение README
GitHub автоматически отобразит содержимое `README_FINAL.md` как главную страницу репозитория.

### 2. Добавление тегов (Topics)
1. На странице репозитория нажмите ⚙️ рядом с "About"
2. Добавьте теги:
   - `django`
   - `python`
   - `document-analysis`
   - `ai`
   - `ollama`
   - `celery`
   - `redis`
   - `bootstrap`

### 3. Настройка описания
В поле "About" добавьте:
```
📊 Система анализа документов с поддержкой AI-анализа через Ollama и асинхронной обработки через Celery
```

---

## 🔄 Ежедневная работа с GitHub

### 1. Загрузка изменений
```bash
# Добавление изменений
git add .

# Коммит изменений
git commit -m "Описание изменений"

# Загрузка на GitHub
git push origin main
```

### 2. Синхронизация с GitHub
```bash
# Получение изменений с GitHub
git pull origin main

# Принудительная синхронизация (осторожно!)
git push --force origin main
```

### 3. Создание веток для новых функций
```bash
# Создание новой ветки
git checkout -b feature/новая-функция

# Переключение на основную ветку
git checkout main

# Слияние ветки
git merge feature/новая-функция
```

---

## 🛡️ Безопасность и приватность

### 1. Файлы, которые НЕ должны попасть на GitHub
Убедитесь, что в `.gitignore` есть:
```
.DS_Store
__pycache__/
*.pyc
*.pyo
*.pyd
.env
.venv
venv/
env/
*.log
db.sqlite3
media/
staticfiles/
```

### 2. Чувствительные данные
```bash
# Если случайно загрузили чувствительные данные:
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/sensitive/file' \
--prune-empty --tag-name-filter cat -- --all
```

---

## 📊 Настройка CI/CD (опционально)

### 1. GitHub Actions
Создайте файл `.github/workflows/django.yml`:
```yaml
name: Django CI

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.13
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        python manage.py test
```

---

## 🎯 Проверочный чек-лист

### ✅ Перед загрузкой:
- [ ] Git настроен (имя и email)
- [ ] Аккаунт GitHub создан
- [ ] Репозиторий на GitHub создан
- [ ] URL репозитория скопирован
- [ ] Все тестовые файлы удалены
- [ ] .gitignore настроен правильно
- [ ] Чувствительные данные не включены

### ✅ После загрузки:
- [ ] Все файлы видны на GitHub
- [ ] README отображается корректно
- [ ] Теги добавлены
- [ ] Описание настроено
- [ ] Аутентификация работает
- [ ] Можно делать push/pull

---

## 🚨 Устранение проблем

### Проблема: "remote origin already exists"
```bash
# Удаление существующего origin
git remote remove origin

# Добавление нового origin
git remote add origin https://github.com/ваш-username/document-analyzer.git
```

### Проблема: "Authentication failed"
```bash
# Проверка настроек Git
git config --global user.name
git config --global user.email

# Обновление URL с токеном
git remote set-url origin https://ваш-username:ваш-токен@github.com/ваш-username/document-analyzer.git
```

### Проблема: "Permission denied"
```bash
# Проверка SSH ключей
ssh -T git@github.com

# Если SSH не работает, используйте HTTPS с токеном
```

---

## 📞 Поддержка

### Полезные команды:
```bash
# Проверка статуса
git status

# Просмотр истории
git log --oneline

# Просмотр удаленных репозиториев
git remote -v

# Информация о ветках
git branch -a
```

### Контакты:
- **GitHub Support**: [support.github.com](https://support.github.com)
- **Git Documentation**: [git-scm.com/doc](https://git-scm.com/doc)
- **Django Documentation**: [docs.djangoproject.com](https://docs.djangoproject.com)

---

## 🎉 Готово!

После выполнения всех шагов ваш проект **📊 Анализатор документов** будет доступен на GitHub и готов для:
- ✅ Совместной работы
- ✅ Открытого исходного кода
- ✅ Автоматического развертывания
- ✅ Отслеживания проблем
- ✅ Управления версиями

**Удачной разработки! 🚀**
