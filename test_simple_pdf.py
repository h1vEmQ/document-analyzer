#!/usr/bin/env python
"""
Простой тест генерации PDF с русским текстом
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from io import BytesIO

def test_simple_pdf():
    """Простой тест генерации PDF с русским текстом"""
    
    print("🔍 Тест простой генерации PDF с русским текстом")
    print("=" * 50)
    
    # Создаем буфер для PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    
    # Получаем стили
    styles = getSampleStyleSheet()
    
    # Собираем элементы
    story = []
    
    # Заголовок
    title = Paragraph("Отчет об изменениях документов", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Информация о документах
    info_text = """
    <b>Базовый документ:</b> Тестовый документ 1<br/>
    <b>Сравниваемый документ:</b> Тестовый документ 2<br/>
    <b>Дата сравнения:</b> 04.10.2025 08:17<br/>
    <b>Пользователь:</b> admin
    """
    info = Paragraph(info_text, styles['Normal'])
    story.append(info)
    story.append(Spacer(1, 20))
    
    # Сводка изменений
    summary_title = Paragraph("Сводка изменений", styles['Heading2'])
    story.append(summary_title)
    story.append(Spacer(1, 10))
    
    # Таблица
    table_data = [
        ['Тип изменения', 'Количество'],
        ['Всего изменений', '16'],
        ['Добавлено', '0'],
        ['Удалено', '10'],
        ['Изменено', '6']
    ]
    
    table = Table(table_data, colWidths=[3*inch, 1.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    story.append(table)
    
    # Генерируем PDF
    doc.build(story)
    
    # Получаем данные
    pdf_data = buffer.getvalue()
    buffer.close()
    
    print(f"✅ PDF сгенерирован успешно!")
    print(f"📏 Размер: {len(pdf_data)} байт")
    
    # Сохраняем файл для проверки
    output_path = '/Users/wind/Documents/WARA/test_simple.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_data)
    
    print(f"📁 Файл сохранен: {output_path}")
    
    # Проверяем содержимое
    russian_text = 'Отчет об изменениях документов'
    if russian_text.encode('utf-8') in pdf_data:
        print(f"✅ Русский текст найден в PDF!")
    else:
        print(f"❌ Русский текст не найден в PDF")
    
    # Проверяем табличные данные
    table_text = 'Всего изменений'
    if table_text.encode('utf-8') in pdf_data:
        print(f"✅ Табличные данные найдены в PDF!")
    else:
        print(f"❌ Табличные данные не найдены в PDF")

if __name__ == '__main__':
    test_simple_pdf()
