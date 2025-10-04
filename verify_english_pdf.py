#!/usr/bin/env python
"""
Проверка английского текста в PDF отчете
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reports.models import Report

def verify_english_pdf():
    """Проверка английского текста в PDF отчете"""
    
    print("🔍 Проверка английского текста в PDF отчете")
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
            
            # Проверяем наличие английских слов в PDF
            english_words = [
                'Document Changes Report',
                'Base Document',
                'Compared Document', 
                'Comparison Date',
                'User',
                'Changes Summary',
                'Change Type',
                'Count',
                'Total Changes',
                'Added',
                'Removed',
                'Modified',
                'Analysis Time',
                'Detailed Changes',
                'Document Metadata',
                'Comparison Information',
                'Created Date',
                'Completed Date',
                'Status',
                'Upload Date',
                'Title',
                'File',
                'Size',
                'Author',
                'Created',
                'Modified',
                'Not specified',
                'Not completed'
            ]
            
            print(f"\n📋 Проверка английских слов в PDF:")
            found_words = 0
            for word in english_words:
                if word.encode('utf-8') in content:
                    print(f"   ✅ Найдено: '{word}'")
                    found_words += 1
                else:
                    print(f"   ❌ Не найдено: '{word}'")
            
            print(f"\n📊 Статистика:")
            print(f"   • Найдено английских слов: {found_words} из {len(english_words)}")
            print(f"   • Процент покрытия: {(found_words/len(english_words)*100):.1f}%")
            
            # Проверяем наличие табличных данных
            table_indicators = [
                'Change Type',
                'Count',
                'Total Changes',
                'Added',
                'Removed',
                'Modified'
            ]
            
            print(f"\n📊 Проверка табличных данных:")
            table_found = 0
            for indicator in table_indicators:
                if indicator.encode('utf-8') in content:
                    print(f"   ✅ Найден индикатор таблицы: '{indicator}'")
                    table_found += 1
                else:
                    print(f"   ❌ Не найден индикатор: '{indicator}'")
            
            print(f"\n📈 Результат проверки таблиц:")
            print(f"   • Найдено индикаторов: {table_found} из {len(table_indicators)}")
            
            # Общий результат
            if found_words >= len(english_words) * 0.8 and table_found >= len(table_indicators) * 0.5:
                print(f"\n🎉 ОТЛИЧНО! PDF отчет содержит корректный английский текст!")
                print(f"   ✅ Английский текст отображается правильно")
                print(f"   ✅ Таблицы содержат нужную информацию")
                print(f"   ✅ Проблема с черными квадратами решена!")
            elif found_words >= len(english_words) * 0.5:
                print(f"\n⚠️ ЧАСТИЧНО: Большая часть английского текста найдена")
                print(f"   ⚠️ Возможны проблемы с некоторыми элементами")
            else:
                print(f"\n❌ ПРОБЛЕМА: Английский текст в PDF не найден")
                print(f"   ❌ Требуется дополнительная настройка")
                
        else:
            print("❌ Файл не является PDF")
            
    else:
        print("❌ PDF файл не найден на диске")

if __name__ == '__main__':
    verify_english_pdf()
