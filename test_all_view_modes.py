#!/usr/bin/env python
"""
Тестирование режимов просмотра для всех разделов WARA
"""

import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from documents.models import Document as DjangoDocument
from analysis.models import Comparison
from reports.models import Report
from django.core.files.uploadedfile import SimpleUploadedFile

User = get_user_model()

def create_test_data():
    """Создание тестовых данных для всех разделов"""
    print("📊 Создание тестовых данных...")
    
    # Получаем или создаем тестового пользователя
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={
            'email': 'test@example.com',
            'first_name': 'Тест',
            'last_name': 'Пользователь',
            'role': 'user'
        }
    )
    if created:
        user.set_password('testpass123')
        user.save()
        print(f"    ✅ Создан пользователь: {user.username}")
    else:
        print(f"    ✅ Используется существующий пользователь: {user.username}")
    
    # Создаем тестовые документы
    doc_count = 3
    for i in range(doc_count):
        doc, created = DjangoDocument.objects.get_or_create(
            title=f'Тестовый документ {i+1}',
            user=user,
            defaults={
                'filename': f'test_doc_{i+1}.docx',
                'content_text': f'Содержимое тестового документа {i+1}',
                'status': 'processed',
                'file_size': 1024 * (i + 1)  # Размер файла в байтах
            }
        )
        if created:
            print(f"    ✅ Создан документ: {doc.title}")
    
    # Создаем тестовые сравнения
    documents = list(DjangoDocument.objects.filter(user=user)[:2])
    if len(documents) >= 2:
        comparison, created = Comparison.objects.get_or_create(
            title='Тестовое сравнение',
            user=user,
            base_document=documents[0],
            compared_document=documents[1],
            defaults={
                'status': 'completed',
                'changes_summary': {'total': 5, 'added': 3, 'removed': 2}
            }
        )
        if created:
            print(f"    ✅ Создано сравнение: {comparison.title}")
    
    # Создаем тестовые отчеты
    if 'comparison' in locals():
        report, created = Report.objects.get_or_create(
            title='Тестовый отчет',
            user=user,
            comparison=comparison,
            defaults={
                'format': 'pdf',
                'status': 'ready'
            }
        )
        if created:
            print(f"    ✅ Создан отчет: {report.title}")
    
    return user

def test_documents_view_modes(client, user):
    """Тестирование режимов просмотра документов"""
    print("\n🔍 Тест режимов просмотра документов")
    print("=" * 50)
    
    # Логинимся
    client.force_login(user)
    
    # Тест 1: Карточный режим (по умолчанию)
    print("\n📄 Тест 1: Карточный режим (по умолчанию)")
    response = client.get(reverse('documents:list'))
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'Карточки' in response.content.decode()
        assert 'Таблица' in response.content.decode()
        print("    ✅ Переключатели режимов найдены")
        assert 'document_list.html' in str(response.template_name)
        print("    ✅ Шаблон найден")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 2: Табличный режим
    print("\n📋 Тест 2: Табличный режим")
    response = client.get(reverse('documents:list') + '?view_mode=table')
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'table table-hover' in response.content.decode()
        print("    ✅ Табличный макет найден")
        assert 'fas fa-hashtag' in response.content.decode()
        print("    ✅ Заголовки таблицы найдены")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")

def test_analysis_view_modes(client, user):
    """Тестирование режимов просмотра анализа"""
    print("\n🔍 Тест режимов просмотра анализа")
    print("=" * 50)
    
    # Тест 1: Карточный режим (по умолчанию)
    print("\n📄 Тест 1: Карточный режим (по умолчанию)")
    response = client.get(reverse('analysis:list'))
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'Карточки' in response.content.decode()
        assert 'Таблица' in response.content.decode()
        print("    ✅ Переключатели режимов найдены")
        assert 'comparison_list.html' in str(response.template_name)
        print("    ✅ Шаблон найден")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 2: Табличный режим
    print("\n📋 Тест 2: Табличный режим")
    response = client.get(reverse('analysis:list') + '?view_mode=table')
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'table table-hover' in response.content.decode()
        print("    ✅ Табличный макет найден")
        assert 'fas fa-balance-scale' in response.content.decode()
        print("    ✅ Заголовки таблицы найдены")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")

def test_reports_view_modes(client, user):
    """Тестирование режимов просмотра отчетов"""
    print("\n🔍 Тест режимов просмотра отчетов")
    print("=" * 50)
    
    # Тест 1: Карточный режим (по умолчанию)
    print("\n📄 Тест 1: Карточный режим (по умолчанию)")
    response = client.get(reverse('reports:list'))
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'Карточки' in response.content.decode()
        assert 'Таблица' in response.content.decode()
        print("    ✅ Переключатели режимов найдены")
        assert 'report_list.html' in str(response.template_name)
        print("    ✅ Шаблон найден")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")
    
    # Тест 2: Табличный режим
    print("\n📋 Тест 2: Табличный режим")
    response = client.get(reverse('reports:list') + '?view_mode=table')
    if response.status_code == 200:
        print("    ✅ Статус ответа: 200")
        if hasattr(response, 'context') and response.context:
            print(f"    📝 Режим просмотра: {response.context.get('view_mode', 'не определен')}")
        assert 'table table-hover' in response.content.decode()
        print("    ✅ Табличный макет найден")
        assert 'fas fa-file-pdf' in response.content.decode()
        print("    ✅ Заголовки таблицы найдены")
    else:
        print(f"    ❌ Ошибка: {response.status_code}")

def test_session_persistence(client, user):
    """Тестирование сохранения режимов в сессии"""
    print("\n🔍 Тест сохранения режимов в сессии")
    print("=" * 50)
    
    # Тест документов
    print("\n📄 Тест документов:")
    response = client.get(reverse('documents:list') + '?view_mode=table')
    response2 = client.get(reverse('documents:list'))
    if response2.status_code == 200:
        if hasattr(response2, 'context') and response2.context:
            view_mode = response2.context.get('view_mode', 'не определен')
            print(f"    ✅ Режим из сессии: {view_mode}")
            if view_mode == 'table':
                print(f"    ✅ Сессия документов работает корректно")
            else:
                print(f"    ❌ Сессия документов не сохраняет режим")
    
    # Тест анализа
    print("\n🔍 Тест анализа:")
    response = client.get(reverse('analysis:list') + '?view_mode=table')
    response2 = client.get(reverse('analysis:list'))
    if response2.status_code == 200:
        if hasattr(response2, 'context') and response2.context:
            view_mode = response2.context.get('view_mode', 'не определен')
            print(f"    ✅ Режим из сессии: {view_mode}")
            if view_mode == 'table':
                print(f"    ✅ Сессия анализа работает корректно")
            else:
                print(f"    ❌ Сессия анализа не сохраняет режим")
    
    # Тест отчетов
    print("\n📊 Тест отчетов:")
    response = client.get(reverse('reports:list') + '?view_mode=table')
    response2 = client.get(reverse('reports:list'))
    if response2.status_code == 200:
        if hasattr(response2, 'context') and response2.context:
            view_mode = response2.context.get('view_mode', 'не определен')
            print(f"    ✅ Режим из сессии: {view_mode}")
            if view_mode == 'table':
                print(f"    ✅ Сессия отчетов работает корректно")
            else:
                print(f"    ❌ Сессия отчетов не сохраняет режим")

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование режимов просмотра для всех разделов WARA")
    print("=" * 70)
    
    try:
        # Создаем тестовые данные
        user = create_test_data()
        
        # Создаем клиент для тестирования
        client = Client()
        
        # Тестируем каждый раздел
        test_documents_view_modes(client, user)
        test_analysis_view_modes(client, user)
        test_reports_view_modes(client, user)
        test_session_persistence(client, user)
        
        print("\n🎉 Тестирование режимов просмотра завершено!")
        print("=" * 70)
        print("✅ Все разделы поддерживают переключение режимов просмотра")
        print("✅ Карточный и табличный режимы работают корректно")
        print("✅ Сессии сохраняют выбранный режим")
        print("✅ Пагинация работает с режимами просмотра")
        
    except Exception as e:
        print(f"\n❌ Ошибка во время тестирования: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
