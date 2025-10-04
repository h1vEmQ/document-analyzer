#!/usr/bin/env python
"""
Тест переключения режимов просмотра документов
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from django.test import Client, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from documents.views import DocumentListView
from documents.models import Document
from django.core.files.base import ContentFile

User = get_user_model()

def create_test_documents(user):
    """Создает тестовые документы для проверки"""
    docs = []
    
    # Создаем несколько тестовых документов
    for i in range(5):
        doc, created = Document.objects.get_or_create(
            user=user,
            title=f'Тестовый документ {i+1}',
            defaults={
                'filename': f'test_document_{i+1}.docx',
                'file': ContentFile(b'dummy content', name=f'test_{i+1}.docx'),
                'file_size': 100 + i * 50,
                'status': 'processed',
                'content_text': f'Это содержимое тестового документа номер {i+1}. Он содержит некоторый текст для проверки отображения в разных режимах просмотра.',
                'metadata': {'author': 'Test User', 'created': '2025-10-04'}
            }
        )
        docs.append(doc)
    
    return docs

def test_view_modes():
    """Тест переключения режимов просмотра"""
    
    print("🧪 Тест переключения режимов просмотра документов")
    print("=" * 60)
    
    # Получаем пользователя
    user = User.objects.first()
    if not user:
        print("❌ Пользователь не найден!")
        return
    
    # Создаем тестовые документы
    docs = create_test_documents(user)
    print(f"📄 Создано тестовых документов: {len(docs)}")
    
    # Создаем тестовый клиент
    client = Client()
    client.force_login(user)
    
    # Тест 1: Карточный режим (по умолчанию)
    print(f"\n🔍 Тест 1: Карточный режим (по умолчанию)")
    response = client.get(reverse('documents:list'))
    
    if response.status_code == 200:
        print(f"    ✅ Статус ответа: {response.status_code}")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        else:
            print(f"    📝 Режим просмотра: не определен")
        
        # Проверяем наличие элементов карточного режима
        content = response.content.decode('utf-8')
        if 'fa-th-large' in content and 'fa-table' in content:
            print(f"    ✅ Переключатели режимов найдены")
        else:
            print(f"    ❌ Переключатели режимов не найдены")
            
        if 'col-lg-4 col-md-6 mb-4' in content:
            print(f"    ✅ Карточный макет найден")
        else:
            print(f"    ❌ Карточный макет не найден")
            
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 2: Табличный режим
    print(f"\n🔍 Тест 2: Табличный режим")
    response = client.get(reverse('documents:list') + '?view_mode=table')
    
    if response.status_code == 200:
        print(f"    ✅ Статус ответа: {response.status_code}")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        else:
            print(f"    📝 Режим просмотра: не определен")
        
        # Проверяем наличие элементов табличного режима
        content = response.content.decode('utf-8')
        if '<table class="table table-hover mb-0">' in content:
            print(f"    ✅ Табличный макет найден")
        else:
            print(f"    ❌ Табличный макет не найден")
            
        if 'thead class="table-light"' in content:
            print(f"    ✅ Заголовки таблицы найдены")
        else:
            print(f"    ❌ Заголовки таблицы не найдены")
            
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 3: Явное указание карточного режима
    print(f"\n🔍 Тест 3: Явное указание карточного режима")
    response = client.get(reverse('documents:list') + '?view_mode=card')
    
    if response.status_code == 200:
        print(f"    ✅ Статус ответа: {response.status_code}")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        else:
            print(f"    📝 Режим просмотра: не определен")
        
        content = response.content.decode('utf-8')
        if 'col-lg-4 col-md-6 mb-4' in content:
            print(f"    ✅ Карточный макет подтвержден")
        else:
            print(f"    ❌ Карточный макет не найден")
            
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 4: Проверка сессии
    print(f"\n🔍 Тест 4: Проверка сохранения в сессии")
    
    # Сначала устанавливаем табличный режим
    response = client.get(reverse('documents:list') + '?view_mode=table')
    
    # Затем запрашиваем без параметров
    response2 = client.get(reverse('documents:list'))
    
    if response2.status_code == 200:
        if hasattr(response2, 'context') and response2.context:
            view_mode = response2.context.get('view_mode', 'не определен')
        else:
            view_mode = 'не определен'
        print(f"    ✅ Режим из сессии: {view_mode}")
        
        if view_mode == 'table':
            print(f"    ✅ Сессия работает корректно")
        else:
            print(f"    ❌ Сессия не сохраняет режим")
    else:
        print(f"    ❌ Ошибка: {response2.status_code}")
    
    # Тест 5: Проверка пагинации с режимами
    print(f"\n🔍 Тест 5: Проверка пагинации с режимами")
    
    # Тестируем пагинацию в табличном режиме
    response = client.get(reverse('documents:list') + '?view_mode=table&page=1')
    
    if response.status_code == 200:
        content = response.content.decode('utf-8')
        if 'view_mode=table' in content:
            print(f"    ✅ Режим сохраняется в пагинации")
        else:
            print(f"    ❌ Режим не сохраняется в пагинации")
    else:
        print(f"    ❌ Ошибка пагинации: {response.status_code}")
    
    print(f"\n🎉 Тестирование режимов просмотра завершено!")
    print(f"📊 Создано тестовых документов: {len(docs)}")

if __name__ == '__main__':
    test_view_modes()
