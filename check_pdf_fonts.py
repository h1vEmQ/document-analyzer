#!/usr/bin/env python
"""
Скрипт для проверки шрифтов в PDF отчете
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reports.models import Report

def check_pdf_fonts():
    """Проверяет шрифты в PDF отчете"""
    
    print("🔍 Проверка шрифтов в PDF отчете")
    print("=" * 40)
    
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
        
        # Проверяем содержимое PDF
        with open(latest_report.file.path, 'rb') as f:
            content = f.read()
            
        # Проверяем, что это PDF
        if content.startswith(b'%PDF'):
            print("✅ Файл является валидным PDF")
            
            # Ищем русские символы в PDF
            russian_text = 'аАбБвВгГдДеЕёЁжЖзЗиИйЙкКлЛмМнНоОпПрРсСтТуУфФхХцЦчЧшШщЩъЪыЫьЬэЭюЮяЯ'
            russian_bytes = russian_text.encode('utf-8')
            found_russian = any(char in content for char in russian_bytes)
            
            if found_russian:
                print("✅ В PDF найдены русские символы")
            else:
                print("❌ В PDF не найдены русские символы")
            
            # Проверяем наличие информации о шрифтах
            if b'/Font' in content:
                print("✅ В PDF найдена информация о шрифтах")
                
                # Ищем упоминания Arial
                if b'Arial' in content:
                    print("✅ В PDF найден шрифт Arial")
                else:
                    print("⚠️ В PDF не найден шрифт Arial")
                    
                # Ищем упоминания Helvetica
                if b'Helvetica' in content:
                    print("✅ В PDF найден шрифт Helvetica")
                else:
                    print("⚠️ В PDF не найден шрифт Helvetica")
            else:
                print("❌ В PDF не найдена информация о шрифтах")
                
        else:
            print("❌ Файл не является PDF")
            
        # Выводим первые 1000 байт для анализа
        print(f"\n📋 Первые 1000 байт содержимого:")
        print(content[:1000].decode('utf-8', errors='ignore'))
        
    else:
        print("❌ PDF файл не найден на диске")

if __name__ == '__main__':
    check_pdf_fonts()
