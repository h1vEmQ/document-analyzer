#!/usr/bin/env python
"""
Тест автоматического заполнения названия сравнения из имен документов
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from analysis.forms import ComparisonCreateForm
from users.models import User
from documents.models import Document
from django.core.files.base import ContentFile

def create_test_documents(user):
    """Создает тестовые документы для проверки"""
    docs = []
    
    # Документ 1
    doc1, created1 = Document.objects.get_or_create(
        user=user,
        title='Отчет за январь 2025',
        defaults={
            'filename': 'Отчет за январь 2025.docx',
            'file': ContentFile(b'dummy content', name='report_january.docx'),
            'file_size': 100,
            'status': 'processed',
            'content_text': 'Тестовый контент документа 1'
        }
    )
    docs.append(doc1)
    
    # Документ 2
    doc2, created2 = Document.objects.get_or_create(
        user=user,
        title='Отчет за февраль 2025',
        defaults={
            'filename': 'Отчет за февраль 2025.docx',
            'file': ContentFile(b'dummy content', name='report_february.docx'),
            'file_size': 120,
            'status': 'processed',
            'content_text': 'Тестовый контент документа 2'
        }
    )
    docs.append(doc2)
    
    # Документ с длинным названием
    doc3, created3 = Document.objects.get_or_create(
        user=user,
        title='Очень длинное название документа для тестирования автоматического заполнения названия сравнения',
        defaults={
            'filename': 'long_name_document.docx',
            'file': ContentFile(b'dummy content', name='long_document.docx'),
            'file_size': 150,
            'status': 'processed',
            'content_text': 'Тестовый контент документа с длинным названием'
        }
    )
    docs.append(doc3)
    
    # Документ с коротким названием
    doc4, created4 = Document.objects.get_or_create(
        user=user,
        title='Краткий отчет',
        defaults={
            'filename': 'short_report.docx',
            'file': ContentFile(b'dummy content', name='short.docx'),
            'file_size': 80,
            'status': 'processed',
            'content_text': 'Краткий контент'
        }
    )
    docs.append(doc4)
    
    return docs

def test_auto_comparison_title():
    """Тест автоматического заполнения названия сравнения"""
    
    print("🧪 Тест автоматического заполнения названия сравнения")
    print("=" * 60)
    
    # Получаем пользователя
    user = User.objects.first()
    if not user:
        print("❌ Пользователь не найден!")
        return
    
    # Создаем тестовые документы
    docs = create_test_documents(user)
    print(f"📄 Создано тестовых документов: {len(docs)}")
    
    # Тест 1: Обычные названия документов
    print(f"\n🔍 Тест 1: Обычные названия документов")
    form_data = {
        'title': '',  # Пустое название
        'base_document': docs[0].id,
        'compared_document': docs[1].id
    }
    
    form = ComparisonCreateForm(user, data=form_data)
    
    if form.is_valid():
        title = form.cleaned_data['title']
        expected_title = f"{docs[0].title} vs {docs[1].title}"
        
        print(f"    ✅ Форма валидна")
        print(f"    📝 Автоматическое название: '{title}'")
        print(f"    🎯 Ожидаемое название: '{expected_title}'")
        
        if title == expected_title:
            print(f"    ✅ Название заполнено корректно!")
        else:
            print(f"    ❌ Название заполнено некорректно!")
    else:
        print(f"    ❌ Форма невалидна: {form.errors}")
    
    # Тест 2: Длинное название документа (должно обрезаться)
    print(f"\n🔍 Тест 2: Длинное название документа")
    form_data2 = {
        'title': '',  # Пустое название
        'base_document': docs[2].id,  # Документ с длинным названием
        'compared_document': docs[3].id  # Документ с коротким названием
    }
    
    form2 = ComparisonCreateForm(user, data=form_data2)
    
    if form2.is_valid():
        title2 = form2.cleaned_data['title']
        expected_base = docs[2].title[:27] + "..." if len(docs[2].title) > 30 else docs[2].title
        expected_title2 = f"{expected_base} vs {docs[3].title}"
        
        print(f"    ✅ Форма валидна")
        print(f"    📝 Автоматическое название: '{title2}'")
        print(f"    🎯 Ожидаемое название: '{expected_title2}'")
        
        if title2 == expected_title2:
            print(f"    ✅ Длинное название корректно обрезано!")
        else:
            print(f"    ❌ Длинное название обработано некорректно!")
    else:
        print(f"    ❌ Форма невалидна: {form2.errors}")
    
    # Тест 3: Пользовательское название (должно сохраниться)
    print(f"\n🔍 Тест 3: Пользовательское название")
    custom_title = "Мое сравнение документов"
    form_data3 = {
        'title': custom_title,  # Заполненное название
        'base_document': docs[0].id,
        'compared_document': docs[1].id
    }
    
    form3 = ComparisonCreateForm(user, data=form_data3)
    
    if form3.is_valid():
        title3 = form3.cleaned_data['title']
        
        print(f"    ✅ Форма валидна")
        print(f"    📝 Название: '{title3}'")
        
        if title3 == custom_title:
            print(f"    ✅ Пользовательское название сохранено!")
        else:
            print(f"    ❌ Пользовательское название не сохранено!")
    else:
        print(f"    ❌ Форма невалидна: {form3.errors}")
    
    # Тест 4: Одинаковые документы (должна быть ошибка)
    print(f"\n🔍 Тест 4: Одинаковые документы")
    form_data4 = {
        'title': '',
        'base_document': docs[0].id,
        'compared_document': docs[0].id  # Одинаковый документ
    }
    
    form4 = ComparisonCreateForm(user, data=form_data4)
    
    if form4.is_valid():
        print(f"    ❌ Форма должна быть невалидна!")
    else:
        print(f"    ✅ Форма корректно отклонена: {form4.errors}")
    
    print(f"\n🎉 Тестирование завершено!")

if __name__ == '__main__':
    test_auto_comparison_title()
