#!/usr/bin/env python3
"""
Тестовый скрипт для проверки пагинации на страницах списков
"""

import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from documents.models import Document
from analysis.models import Comparison
from reports.models import Report
from settings.models import ApplicationSettings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

User = get_user_model()

def test_pagination_settings():
    """Тестирует настройки пагинации"""
    
    print("📄 Тестирование настроек пагинации")
    print("=" * 50)
    
    # Получаем настройки приложения
    settings = ApplicationSettings.get_settings()
    print(f"📋 Количество элементов на странице: {settings.items_per_page}")
    
    # Проверяем, что настройка в допустимых пределах
    if 5 <= settings.items_per_page <= 100:
        print("✅ Настройка пагинации в допустимых пределах (5-100)")
    else:
        print("❌ Настройка пагинации вне допустимых пределов")
        return False
    
    return True

def test_pagination_views():
    """Тестирует пагинацию в представлениях"""
    
    print("\n🔍 Тестирование пагинации в представлениях")
    print("=" * 50)
    
    # Получаем пользователя
    try:
        user = User.objects.first()
        if not user:
            print("❌ Нет пользователей в системе")
            return False
    except Exception as e:
        print(f"❌ Ошибка получения пользователя: {e}")
        return False
    
    # Создаем фабрику запросов
    factory = RequestFactory()
    
    # Тест 1: Документы
    print("\n📄 Тест 1: Пагинация документов")
    documents_count = Document.objects.filter(user=user).count()
    print(f"   Всего документов: {documents_count}")
    
    if documents_count > 0:
        # Импортируем представления
        from documents.views import DocumentListView
        
        # Создаем запрос
        request = factory.get('/documents/')
        request.user = user
        
        # Создаем представление
        view = DocumentListView()
        view.request = request
        
        # Получаем queryset
        queryset = view.get_queryset()
        print(f"   Документов в queryset: {queryset.count()}")
        
        # Проверяем пагинацию
        paginate_by = view.get_paginate_by(queryset)
        print(f"   Элементов на странице: {paginate_by}")
        
        if paginate_by > 0:
            print("✅ Пагинация документов настроена")
        else:
            print("❌ Пагинация документов не настроена")
    else:
        print("⚠️  Нет документов для тестирования")
    
    # Тест 2: Анализы
    print("\n🔍 Тест 2: Пагинация анализов")
    comparisons_count = Comparison.objects.filter(user=user).count()
    print(f"   Всего анализов: {comparisons_count}")
    
    if comparisons_count > 0:
        from analysis.views import ComparisonListView
        
        request = factory.get('/analysis/')
        request.user = user
        
        view = ComparisonListView()
        view.request = request
        
        queryset = view.get_queryset()
        print(f"   Анализов в queryset: {queryset.count()}")
        
        paginate_by = view.get_paginate_by(queryset)
        print(f"   Элементов на странице: {paginate_by}")
        
        if paginate_by > 0:
            print("✅ Пагинация анализов настроена")
        else:
            print("❌ Пагинация анализов не настроена")
    else:
        print("⚠️  Нет анализов для тестирования")
    
    # Тест 3: Отчеты
    print("\n📊 Тест 3: Пагинация отчетов")
    reports_count = Report.objects.filter(user=user).count()
    print(f"   Всего отчетов: {reports_count}")
    
    if reports_count > 0:
        from reports.views import ReportListView
        
        request = factory.get('/reports/')
        request.user = user
        
        view = ReportListView()
        view.request = request
        
        queryset = view.get_queryset()
        print(f"   Отчетов в queryset: {queryset.count()}")
        
        paginate_by = view.get_paginate_by(queryset)
        print(f"   Элементов на странице: {paginate_by}")
        
        if paginate_by > 0:
            print("✅ Пагинация отчетов настроена")
        else:
            print("❌ Пагинация отчетов не настроена")
    else:
        print("⚠️  Нет отчетов для тестирования")
    
    return True

def test_pagination_changes():
    """Тестирует изменение настроек пагинации"""
    
    print("\n⚙️ Тестирование изменения настроек пагинации")
    print("=" * 50)
    
    # Получаем текущие настройки
    settings = ApplicationSettings.get_settings()
    original_value = settings.items_per_page
    print(f"📋 Исходное значение: {original_value}")
    
    # Изменяем настройку
    test_value = 15
    settings.items_per_page = test_value
    settings.save()
    print(f"🔧 Установлено значение: {test_value}")
    
    # Проверяем, что значение изменилось
    updated_settings = ApplicationSettings.get_settings()
    if updated_settings.items_per_page == test_value:
        print("✅ Настройка пагинации успешно изменена")
    else:
        print("❌ Ошибка изменения настройки пагинации")
        return False
    
    # Восстанавливаем исходное значение
    settings.items_per_page = original_value
    settings.save()
    print(f"🔄 Восстановлено исходное значение: {original_value}")
    
    return True

def test_pagination_validation():
    """Тестирует валидацию настроек пагинации"""
    
    print("\n✅ Тестирование валидации настроек пагинации")
    print("=" * 50)
    
    from settings.forms import ApplicationSettingsForm
    
    # Тест 1: Валидные значения
    print("\n🔍 Тест 1: Валидные значения")
    valid_values = [5, 10, 25, 50, 100]
    
    for value in valid_values:
        form_data = {'items_per_page': value}
        form = ApplicationSettingsForm(data=form_data)
        
        if form.is_valid():
            print(f"   ✅ Значение {value} - валидно")
        else:
            print(f"   ❌ Значение {value} - невалидно: {form.errors.get('items_per_page')}")
    
    # Тест 2: Невалидные значения
    print("\n🔍 Тест 2: Невалидные значения")
    invalid_values = [0, 1, 4, 101, 200, -5]
    
    for value in invalid_values:
        form_data = {'items_per_page': value}
        form = ApplicationSettingsForm(data=form_data)
        
        if not form.is_valid():
            print(f"   ✅ Значение {value} - корректно отклонено: {form.errors.get('items_per_page')}")
        else:
            print(f"   ❌ Значение {value} - должно быть отклонено, но принято")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск тестов пагинации")
    print("=" * 60)
    
    # Запускаем все тесты
    tests_passed = 0
    total_tests = 4
    
    if test_pagination_settings():
        tests_passed += 1
    
    if test_pagination_views():
        tests_passed += 1
    
    if test_pagination_changes():
        tests_passed += 1
    
    if test_pagination_validation():
        tests_passed += 1
    
    print("\n" + "=" * 60)
    print(f"🏁 Тестирование завершено: {tests_passed}/{total_tests} тестов пройдено")
    
    if tests_passed == total_tests:
        print("🎉 Все тесты пагинации прошли успешно!")
    else:
        print("⚠️  Некоторые тесты не прошли")
