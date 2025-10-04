#!/usr/bin/env python
"""
Проверка файлов отчетов в базе данных
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reports.models import Report

def check_report_files():
    """Проверка файлов отчетов"""
    
    print("📁 Проверка файлов отчетов в базе данных")
    print("=" * 50)
    
    # Получаем все отчеты
    reports = Report.objects.all().order_by('-generated_date')
    
    if not reports.exists():
        print("❌ Отчеты не найдены!")
        return
    
    print(f"📊 Найдено отчетов: {reports.count()}")
    print()
    
    for i, report in enumerate(reports, 1):
        print(f"📄 Отчет #{i} (ID: {report.id}):")
        print(f"   • Название: {report.title}")
        print(f"   • Формат: {report.format}")
        print(f"   • Дата создания: {report.generated_date}")
        
        if report.file:
            print(f"   • Файл в БД: {report.file.name}")
            print(f"   • Полный путь: {report.file.path}")
            
            # Проверяем, существует ли файл на диске
            if os.path.exists(report.file.path):
                file_size = os.path.getsize(report.file.path)
                print(f"   • Размер файла: {file_size} байт")
                print(f"   • Статус: ✅ Файл существует")
                
                # Проверяем расширение
                filename = os.path.basename(report.file.path)
                if filename.endswith('.pdf'):
                    print(f"   • Расширение: ✅ .pdf")
                else:
                    print(f"   • Расширение: ❌ {filename.split('.')[-1] if '.' in filename else 'нет расширения'}")
                    
            else:
                print(f"   • Статус: ❌ Файл не найден на диске")
        else:
            print(f"   • Файл: ❌ Не прикреплен")
        
        print()

if __name__ == '__main__':
    check_report_files()
