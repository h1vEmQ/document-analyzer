#!/usr/bin/env python3
"""
Тестовый скрипт для проверки ответов Ollama на русском языке
"""

import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from analysis.ollama_service import OllamaService

def test_russian_responses():
    """Тестирует ответы Ollama на русском языке"""
    
    print("🇷🇺 Тестирование ответов Ollama на русском языке")
    print("=" * 50)
    
    # Инициализация сервиса
    ollama_service = OllamaService(model="llama3")
    
    # Проверка доступности
    if not ollama_service.is_available():
        print("❌ Ollama сервис недоступен")
        print("Убедитесь, что Ollama запущен на localhost:11434")
        return False
    
    print("✅ Ollama сервис доступен")
    
    # Получение списка моделей
    models = ollama_service.get_available_models()
    print(f"📋 Доступные модели: {models}")
    
    if not models:
        print("❌ Нет доступных моделей")
        return False
    
    # Тест 1: Анализ тональности
    print("\n🔍 Тест 1: Анализ тональности")
    test_text = "Это отличный документ с положительными отзывами и хорошими результатами."
    
    sentiment_result = ollama_service.analyze_document_sentiment(test_text)
    
    if sentiment_result["success"]:
        print("✅ Анализ тональности выполнен")
        print(f"📊 Результат: {sentiment_result['sentiment_result']}")
    else:
        print("❌ Ошибка анализа тональности")
        print(f"Ошибка: {sentiment_result.get('error', 'Неизвестная ошибка')}")
    
    # Тест 2: Извлечение ключевых моментов
    print("\n🔍 Тест 2: Извлечение ключевых моментов")
    test_document = """
    Отчет о работе за квартал.
    
    Основные достижения:
    1. Увеличение продаж на 25%
    2. Запуск нового продукта
    3. Расширение команды на 5 человек
    
    Проблемы:
    1. Задержки в поставках
    2. Повышение цен на сырье
    
    Планы на следующий квартал:
    1. Оптимизация процессов
    2. Внедрение новых технологий
    """
    
    key_points_result = ollama_service.extract_key_points(test_document)
    
    if key_points_result["success"]:
        print("✅ Извлечение ключевых моментов выполнено")
        print(f"📊 Результат: {key_points_result['key_points_result']}")
    else:
        print("❌ Ошибка извлечения ключевых моментов")
        print(f"Ошибка: {key_points_result.get('error', 'Неизвестная ошибка')}")
    
    # Тест 3: Сравнение документов
    print("\n🔍 Тест 3: Сравнение документов")
    
    doc1 = "Первый документ содержит информацию о проекте А. Бюджет составляет 100000 рублей."
    doc2 = "Второй документ содержит информацию о проекте Б. Бюджет составляет 150000 рублей."
    
    comparison_result = ollama_service.compare_documents(
        doc1, doc2, "Проект А", "Проект Б"
    )
    
    if comparison_result["success"]:
        print("✅ Сравнение документов выполнено")
        print(f"📊 Результат: {comparison_result['comparison_result']}")
    else:
        print("❌ Ошибка сравнения документов")
        print(f"Ошибка: {comparison_result.get('error', 'Неизвестная ошибка')}")
    
    print("\n" + "=" * 50)
    print("🏁 Тестирование завершено")
    
    return True

if __name__ == "__main__":
    test_russian_responses()
