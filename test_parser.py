#!/usr/bin/env python
"""
Скрипт для тестирования парсера документов
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from documents.services import DocumentParserService, DocumentValidationService
from documents.models import Document
from django.core.files import File
import tempfile

def test_document_parser():
    """Тестирование парсера документов"""
    
    print("🧪 Тестирование парсера документов WARA")
    print("=" * 50)
    
    # Находим тестовый документ
    test_files = [f for f in os.listdir('/Users/wind/Documents/WARA') if f.startswith('test_document_') and f.endswith('.docx')]
    
    if not test_files:
        print("❌ Тестовый документ не найден!")
        return
    
    test_file = test_files[-1]  # Берем последний созданный
    file_path = os.path.join('/Users/wind/Documents/WARA', test_file)
    
    print(f"📄 Тестовый файл: {test_file}")
    print(f"📏 Размер: {os.path.getsize(file_path)} байт")
    
    # Тестируем валидацию
    print("\n🔍 Тестирование валидации файла...")
    validation_service = DocumentValidationService()
    
    with open(file_path, 'rb') as f:
        from django.core.files.uploadedfile import SimpleUploadedFile
        uploaded_file = SimpleUploadedFile(
            name=test_file,
            content=f.read(),
            content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        )
        
        validation_result = validation_service.validate_upload(uploaded_file)
        
        print(f"✅ Валидность: {validation_result['is_valid']}")
        if validation_result['errors']:
            print(f"❌ Ошибки: {validation_result['errors']}")
        if validation_result['warnings']:
            print(f"⚠️ Предупреждения: {validation_result['warnings']}")
        
        print(f"📊 Информация о файле: {validation_result['file_info']}")
    
    # Создаем тестовый документ в БД
    print("\n💾 Создание тестового документа в БД...")
    
    # Получаем пользователя
    from users.models import User
    user = User.objects.first()
    if not user:
        print("❌ Пользователь не найден! Создайте пользователя сначала.")
        return
    
    with open(file_path, 'rb') as f:
        django_file = File(f, name=test_file)  # Указываем только имя файла
        test_document = Document(
            title=f"Тестовый документ - {test_file}",
            filename=test_file,
            file=django_file,
            file_size=os.path.getsize(file_path),
            user=user
        )
        test_document.save()
        
        print(f"✅ Документ создан с ID: {test_document.id}")
    
    # Тестируем парсинг
    print("\n🔧 Тестирование парсинга документа...")
    
    try:
        parser_service = DocumentParserService()
        content_data = parser_service.parse_document(test_document)
        
        print("✅ Парсинг успешно завершен!")
        
        # Выводим результаты
        print(f"\n📊 Результаты парсинга:")
        print(f"📝 Длина текста: {len(content_data['text_content'])} символов")
        print(f"📑 Количество разделов: {len(content_data['sections'])}")
        print(f"📋 Количество таблиц: {len(content_data['tables'])}")
        
        # Показываем структуру
        if content_data['structure']:
            print(f"\n🏗️ Структура документа:")
            print(f"   • Всего абзацев: {content_data['structure']['total_paragraphs']}")
            print(f"   • Всего таблиц: {content_data['structure']['total_tables']}")
            print(f"   • Уровни заголовков: {content_data['structure']['heading_levels']}")
            print(f"   • Примерное количество страниц: {content_data['structure']['estimated_pages']}")
        
        # Показываем метаданные
        if content_data['metadata']:
            print(f"\n📋 Метаданные:")
            for key, value in content_data['metadata'].items():
                if value:
                    print(f"   • {key}: {value}")
        
        # Показываем первые несколько разделов
        if content_data['sections']:
            print(f"\n📑 Первые разделы:")
            for i, section in enumerate(content_data['sections'][:3]):
                print(f"   {i+1}. {section['title']} (уровень {section['level']})")
                print(f"      Содержимое: {section['content'][:100]}...")
        
        # Показываем таблицы
        if content_data['tables']:
            print(f"\n📋 Таблицы:")
            for i, table in enumerate(content_data['tables']):
                print(f"   {i+1}. {table['title']} ({table['row_count']} строк, {table['col_count']} столбцов)")
                if table['headers']:
                    print(f"      Заголовки: {', '.join(table['headers'])}")
        
        # Сохраняем результаты в БД
        print(f"\n💾 Сохранение результатов в БД...")
        parser_service.save_parsed_content(test_document, content_data)
        
        # Проверяем сохранение
        test_document.refresh_from_db()
        print(f"✅ Статус документа: {test_document.status}")
        print(f"✅ Разделов в БД: {test_document.get_parsed_sections_count()}")
        print(f"✅ Таблиц в БД: {test_document.get_parsed_tables_count()}")
        
    except Exception as e:
        print(f"❌ Ошибка при парсинге: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print(f"\n🎉 Тестирование завершено!")
    print(f"📄 Тестовый документ ID: {test_document.id}")

if __name__ == '__main__':
    test_document_parser()
