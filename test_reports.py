#!/usr/bin/env python
"""
Скрипт для тестирования системы генерации отчетов
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reports.services import PDFReportGeneratorService, EmailReportService, ReportTemplateService
from reports.models import Report, ReportTemplate
from analysis.models import Comparison
from documents.models import Document as DjangoDocument
from users.models import User
from django.utils import timezone
from django.core.files.base import ContentFile

def test_report_generation():
    """Тестирование системы генерации отчетов"""
    
    print("📊 Тестирование системы генерации отчетов WARA")
    print("=" * 60)
    
    # Получаем пользователя
    user = User.objects.first()
    if not user:
        print("❌ Пользователь не найден!")
        return
    
    # Получаем завершенное сравнение
    completed_comparison = Comparison.objects.filter(
        user=user,
        status='completed'
    ).first()
    
    if not completed_comparison:
        print("❌ Завершенное сравнение не найдено!")
        print("   Сначала создайте и завершите сравнение документов")
        return
    
    print(f"📄 Используем сравнение: {completed_comparison.id}")
    print(f"   Базовый документ: {completed_comparison.base_document.title}")
    print(f"   Сравниваемый документ: {completed_comparison.compared_document.title}")
    
    # Тестируем генерацию PDF отчета
    print("\n🔧 Тестирование генерации PDF отчета...")
    
    try:
        pdf_service = PDFReportGeneratorService()
        
        # Генерируем PDF
        start_time = timezone.now()
        pdf_data = pdf_service.generate_comparison_report(completed_comparison)
        end_time = timezone.now()
        
        generation_time = (end_time - start_time).total_seconds()
        
        print("✅ PDF отчет сгенерирован успешно!")
        print(f"⏱️ Время генерации: {generation_time:.2f} секунд")
        print(f"📏 Размер PDF: {len(pdf_data)} байт")
        
        # Создаем отчет в БД
        report = Report.objects.create(
            user=user,
            comparison=completed_comparison,
            title=f"Тестовый отчет: {completed_comparison.base_document.title} vs {completed_comparison.compared_document.title}",
            format='pdf',
            file=ContentFile(pdf_data, name=f"test_report_{completed_comparison.id}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.pdf"),
            template_used='default',
            status='ready'
        )
        
        print(f"✅ Отчет создан в БД с ID: {report.id}")
        print(f"📁 Файл: {report.file.name}")
        
    except Exception as e:
        print(f"❌ Ошибка при генерации PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Тестируем шаблоны отчетов
    print(f"\n📋 Тестирование шаблонов отчетов...")
    
    try:
        template_service = ReportTemplateService()
        default_template = template_service.get_default_template()
        
        print(f"✅ Шаблон по умолчанию:")
        print(f"   • ID: {default_template.id}")
        print(f"   • Название: {default_template.name}")
        print(f"   • По умолчанию: {default_template.is_default}")
        print(f"   • Размер содержимого: {len(default_template.template_content)} символов")
        
    except Exception as e:
        print(f"❌ Ошибка при работе с шаблонами: {str(e)}")
    
    # Тестируем отправку email
    print(f"\n📧 Тестирование отправки email...")
    
    try:
        email_service = EmailReportService()
        
        # Тестовая отправка (в режиме разработки)
        test_email = "test@example.com"
        result = email_service.send_report_email(report, test_email, "Тестовое сообщение")
        
        if result['success']:
            print("✅ Email отправлен успешно!")
        else:
            print(f"⚠️ Email не отправлен: {result['message']}")
        
        print(f"📧 Результат отправки: {result}")
        
    except Exception as e:
        print(f"❌ Ошибка при отправке email: {str(e)}")
    
    # Показываем статистику отчета
    print(f"\n📊 Статистика отчета:")
    print(f"   • ID отчета: {report.id}")
    print(f"   • Название: {report.title}")
    print(f"   • Формат: {report.format}")
    print(f"   • Дата генерации: {report.generated_date}")
    print(f"   • Размер файла: {len(pdf_data)} байт")
    print(f"   • Связанное сравнение: {report.comparison.id}")
    
    if report.comparison.changes_summary:
        summary = report.comparison.changes_summary
        print(f"   • Сводка изменений:")
        print(f"     - Всего: {summary.get('total', 0)}")
        print(f"     - Добавлено: {summary.get('added', 0)}")
        print(f"     - Удалено: {summary.get('removed', 0)}")
        print(f"     - Изменено: {summary.get('modified', 0)}")
    
    # Проверяем уведомления email
    email_notifications = report.email_notifications.all()
    if email_notifications.exists():
        print(f"\n📬 Email уведомления:")
        for notification in email_notifications:
            status_text = "✅ Отправлено" if notification.status == 'sent' else "❌ Не отправлено"
            print(f"   • {notification.recipient_email}: {status_text}")
            if notification.status == 'failed':
                print(f"     Статус: {notification.status}")
    
    print(f"\n🎉 Тестирование генерации отчетов завершено!")
    print(f"📄 Отчет ID: {report.id}")

def test_pdf_content():
    """Тестирование содержимого PDF отчета"""
    
    print("\n🔍 Анализ содержимого PDF отчета...")
    
    try:
        # Находим последний созданный отчет
        latest_report = Report.objects.filter(format='pdf').order_by('-generated_date').first()
        
        if not latest_report:
            print("❌ PDF отчет не найден!")
            return
        
        print(f"📄 Анализируем отчет: {latest_report.title}")
        
        # Читаем PDF файл
        if latest_report.file and os.path.exists(latest_report.file.path):
            with open(latest_report.file.path, 'rb') as f:
                pdf_content = f.read()
                
            print(f"✅ PDF файл найден")
            print(f"📏 Размер: {len(pdf_content)} байт")
            
            # Проверяем, что это действительно PDF
            if pdf_content.startswith(b'%PDF'):
                print("✅ Файл является валидным PDF")
            else:
                print("❌ Файл не является PDF")
                
        else:
            print("❌ PDF файл не найден на диске")
            
    except Exception as e:
        print(f"❌ Ошибка при анализе PDF: {str(e)}")

if __name__ == '__main__':
    # Основное тестирование
    test_report_generation()
    
    # Анализ содержимого
    test_pdf_content()
