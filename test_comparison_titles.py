#!/usr/bin/env python3
"""
Тестовый скрипт для проверки заголовков сравнений с версиями
"""

import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from analysis.models import Comparison
from analysis.forms import ComparisonCreateForm
from documents.models import Document
from django.contrib.auth import get_user_model

User = get_user_model()

def test_comparison_titles():
    """Тестирует заголовки сравнений с версиями"""
    
    print("🔍 Тестирование заголовков сравнений с версиями")
    print("=" * 60)
    
    # Получаем пользователя
    try:
        user = User.objects.first()
        if not user:
            print("❌ Нет пользователей в системе")
            return False
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return False
    
    # Получаем документы
    documents = Document.objects.all()[:5]
    if len(documents) < 2:
        print("❌ Недостаточно документов для тестирования (нужно минимум 2)")
        return False
    
    print(f"📋 Найдено документов: {len(documents)}")
    
    # Тест 1: Сравнение разных документов
    print("\n🔍 Тест 1: Сравнение разных документов")
    base_doc = documents[0]
    compared_doc = documents[1]
    
    print(f"📄 Базовый документ: {base_doc.title} (v{base_doc.version})")
    print(f"📄 Сравниваемый документ: {compared_doc.title} (v{compared_doc.version})")
    
    # Создаем форму
    form_data = {
        'base_document': base_doc.id,
        'compared_document': compared_doc.id,
        'title': '',  # Пустое название для автозаполнения
    }
    
    form = ComparisonCreateForm(user=user, data=form_data)
    
    if form.is_valid():
        expected_title = form.cleaned_data.get('title')
        print(f"✅ Ожидаемый заголовок: {expected_title}")
        
        # Проверяем, что версии присутствуют в заголовке
        if f"v{base_doc.version}" in expected_title and f"v{compared_doc.version}" in expected_title:
            print("✅ Версии документов присутствуют в заголовке")
        else:
            print("❌ Версии документов отсутствуют в заголовке")
            print(f"   Найденные версии: v{base_doc.version}, v{compared_doc.version}")
            return False
    else:
        print("❌ Форма невалидна:")
        for field, errors in form.errors.items():
            print(f"   {field}: {errors}")
        return False
    
    # Тест 2: Проверка существующих сравнений
    print("\n🔍 Тест 2: Существующие сравнения")
    comparisons = Comparison.objects.filter(user=user).order_by('-created_date')[:5]
    
    if comparisons:
        print(f"📋 Найдено сравнений: {len(comparisons)}")
        for i, comparison in enumerate(comparisons, 1):
            print(f"   {i}. {comparison.title}")
            
            # Проверяем, что версии присутствуют в заголовке
            base_version = comparison.base_document.version
            compared_version = comparison.compared_document.version
            
            if f"v{base_version}" in comparison.title and f"v{compared_version}" in comparison.title:
                print(f"      ✅ Версии присутствуют: v{base_version}, v{compared_version}")
            else:
                print(f"      ⚠️  Версии могут отсутствовать: v{base_version}, v{compared_version}")
    else:
        print("📋 Нет существующих сравнений")
    
    # Тест 3: Сравнение версий одного документа
    print("\n🔍 Тест 3: Сравнение версий одного документа")
    
    # Ищем документы с родительским документом
    versioned_docs = Document.objects.filter(parent_document__isnull=False)[:2]
    
    if len(versioned_docs) >= 2:
        version_doc1 = versioned_docs[0]
        version_doc2 = versioned_docs[1]
        
        # Проверяем, что это версии одного документа
        if version_doc1.parent_document == version_doc2.parent_document:
            print(f"📄 Версия 1: {version_doc1.title} (v{version_doc1.version})")
            print(f"📄 Версия 2: {version_doc2.title} (v{version_doc2.version})")
            print(f"📄 Родительский документ: {version_doc1.parent_document.title}")
            
            form_data = {
                'base_document': version_doc1.id,
                'compared_document': version_doc2.id,
                'title': '',
            }
            
            form = ComparisonCreateForm(user=user, data=form_data)
            
            if form.is_valid():
                expected_title = form.cleaned_data.get('title')
                print(f"✅ Ожидаемый заголовок: {expected_title}")
                
                # Проверяем формат для версий
                if "→" in expected_title:
                    print("✅ Использован формат сравнения версий (→)")
                else:
                    print("⚠️  Не используется формат сравнения версий")
            else:
                print("❌ Форма невалидна для версий:")
                for field, errors in form.errors.items():
                    print(f"   {field}: {errors}")
        else:
            print("⚠️  Не найдены версии одного документа для тестирования")
    else:
        print("⚠️  Не найдены документы с версиями для тестирования")
    
    print("\n" + "=" * 60)
    print("🏁 Тестирование завершено")
    
    return True

if __name__ == "__main__":
    test_comparison_titles()
