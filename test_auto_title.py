#!/usr/bin/env python
"""
Тест автоматического заполнения названия документа из имени файла
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from documents.forms import DocumentUploadForm
from django.core.files.uploadedfile import SimpleUploadedFile

def test_auto_title():
    """Тест автоматического заполнения названия документа"""
    
    print("🧪 Тест автоматического заполнения названия документа")
    print("=" * 60)
    
    # Тестовые данные
    test_files = [
        "Отчет за январь 2025.docx",
        "monthly_report.docx", 
        "document_with_long_name_and_special_chars_2025.docx",
        "simple.docx"
    ]
    
    for filename in test_files:
        print(f"\n📄 Тестируем файл: {filename}")
        
        # Создаем тестовый файл
        test_content = b"Test content for document"
        uploaded_file = SimpleUploadedFile(
            name=filename,
            content=test_content,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        # Тест 1: Пустое название (должно заполниться автоматически)
        print("  🔍 Тест 1: Пустое название")
        form_data = {
            'title': '',  # Пустое название
            'file': uploaded_file
        }
        
        form = DocumentUploadForm(data={'title': ''}, files={'file': uploaded_file})
        
        if form.is_valid():
            title = form.cleaned_data['title']
            expected_title = filename.rsplit('.', 1)[0]  # Убираем расширение
            
            print(f"    ✅ Форма валидна")
            print(f"    📝 Автоматическое название: '{title}'")
            print(f"    🎯 Ожидаемое название: '{expected_title}'")
            
            if title == expected_title:
                print(f"    ✅ Название заполнено корректно!")
            else:
                print(f"    ❌ Название заполнено некорректно!")
        else:
            print(f"    ❌ Форма невалидна: {form.errors}")
        
        # Тест 2: Заполненное название (должно остаться как есть)
        print("  🔍 Тест 2: Заполненное название")
        custom_title = "Мой документ"
        
        uploaded_file2 = SimpleUploadedFile(
            name=filename,
            content=test_content,
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        form2 = DocumentUploadForm(data={'title': custom_title}, files={'file': uploaded_file2})
        
        if form2.is_valid():
            title2 = form2.cleaned_data['title']
            print(f"    ✅ Форма валидна")
            print(f"    📝 Название: '{title2}'")
            
            if title2 == custom_title:
                print(f"    ✅ Пользовательское название сохранено!")
            else:
                print(f"    ❌ Пользовательское название не сохранено!")
        else:
            print(f"    ❌ Форма невалидна: {form2.errors}")
        
        print(f"  {'='*40}")

if __name__ == '__main__':
    test_auto_title()
