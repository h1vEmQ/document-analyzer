#!/usr/bin/env python
"""
Скрипт для детальной проверки содержимого PDF отчета
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reports.models import Report
import re

def verify_pdf_content():
    """Детальная проверка содержимого PDF отчета"""
    
    print("🔍 Детальная проверка содержимого PDF отчета")
    print("=" * 50)
    
    # Находим последний PDF отчет
    latest_report = Report.objects.filter(format='pdf').order_by('-generated_date').first()
    
    if not latest_report:
        print("❌ PDF отчет не найден!")
        return
    
    print(f"📄 Проверяем отчет: {latest_report.title}")
    print(f"📁 Файл: {latest_report.file.name}")
    
    if latest_report.file and os.path.exists(latest_report.file.path):
        file_size = os.path.getsize(latest_report.file.path)
        print(f"📏 Размер файла: {file_size} байт")
        
        # Читаем содержимое PDF
        with open(latest_report.file.path, 'rb') as f:
            content = f.read()
            
        if content.startswith(b'%PDF'):
            print("✅ Файл является валидным PDF")
            
            # Проверяем наличие русских слов в PDF
            russian_words = [
                'Отчет об изменениях документов',
                'Базовый документ',
                'Сравниваемый документ', 
                'Дата сравнения',
                'Пользователь',
                'Сводка изменений',
                'Всего изменений',
                'Добавлено',
                'Удалено',
                'Изменено',
                'Время анализа',
                'Детальные изменения',
                'Метаданные документов',
                'Информация о сравнении',
                'Дата создания',
                'Дата завершения',
                'Статус'
            ]
            
            print(f"\n📋 Проверка русских слов в PDF:")
            found_words = 0
            for word in russian_words:
                word_bytes = word.encode('utf-8')
                if word_bytes in content:
                    print(f"   ✅ Найдено: '{word}'")
                    found_words += 1
                else:
                    print(f"   ❌ Не найдено: '{word}'")
            
            print(f"\n📊 Статистика:")
            print(f"   • Найдено русских слов: {found_words} из {len(russian_words)}")
            print(f"   • Процент покрытия: {(found_words/len(russian_words)*100):.1f}%")
            
            # Проверяем наличие табличных данных
            table_indicators = [
                'Всего изменений',
                'Добавлено',
                'Удалено', 
                'Изменено'
            ]
            
            print(f"\n📊 Проверка табличных данных:")
            table_found = 0
            for indicator in table_indicators:
                indicator_bytes = indicator.encode('utf-8')
                if indicator_bytes in content:
                    print(f"   ✅ Найден индикатор таблицы: '{indicator}'")
                    table_found += 1
                else:
                    print(f"   ❌ Не найден индикатор: '{indicator}'")
            
            print(f"\n📈 Результат проверки таблиц:")
            print(f"   • Найдено индикаторов: {table_found} из {len(table_indicators)}")
            
            # Общий результат
            if found_words >= len(russian_words) * 0.8 and table_found >= len(table_indicators) * 0.5:
                print(f"\n🎉 ОТЛИЧНО! PDF отчет содержит корректный русский текст!")
                print(f"   ✅ Русский текст отображается правильно")
                print(f"   ✅ Таблицы содержат нужную информацию")
                print(f"   ✅ Проблема с черными квадратами решена")
            elif found_words >= len(russian_words) * 0.5:
                print(f"\n⚠️ ЧАСТИЧНО: Большая часть русского текста найдена")
                print(f"   ⚠️ Возможны проблемы с некоторыми элементами")
            else:
                print(f"\n❌ ПРОБЛЕМА: Русский текст в PDF не найден")
                print(f"   ❌ Требуется дополнительная настройка шрифтов")
                
        else:
            print("❌ Файл не является PDF")
            
    else:
        print("❌ PDF файл не найден на диске")

if __name__ == '__main__':
    verify_pdf_content()
