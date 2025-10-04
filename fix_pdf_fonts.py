#!/usr/bin/env python
"""
Исправление проблемы с шрифтами в PDF отчетах
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from io import BytesIO

def register_russian_fonts():
    """Регистрация шрифтов с поддержкой кириллицы"""
    
    print("🔧 Регистрация шрифтов с поддержкой кириллицы")
    
    # Попробуем найти системные шрифты
    font_paths = [
        # macOS
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        # Windows (если запущено на Windows)
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        # Linux
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    
    registered_fonts = []
    
    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                # Регистрируем обычный шрифт
                pdfmetrics.registerFont(TTFont('RussianFont', font_path))
                registered_fonts.append(('RussianFont', font_path))
                print(f"✅ Зарегистрирован шрифт: {font_path}")
                
                # Пытаемся найти жирную версию
                bold_path = font_path.replace('.ttf', '-Bold.ttf').replace('.ttc', '-Bold.ttf')
                if os.path.exists(bold_path):
                    pdfmetrics.registerFont(TTFont('RussianFont-Bold', bold_path))
                    registered_fonts.append(('RussianFont-Bold', bold_path))
                    print(f"✅ Зарегистрирован жирный шрифт: {bold_path}")
                
                return registered_fonts
                
            except Exception as e:
                print(f"❌ Ошибка при регистрации {font_path}: {e}")
                continue
    
    print("⚠️ Системные шрифты не найдены, используем встроенные")
    return []

def create_russian_styles():
    """Создание стилей с поддержкой русского языка"""
    
    styles = getSampleStyleSheet()
    
    # Создаем стиль для русского текста
    russian_style = ParagraphStyle(
        'RussianText',
        parent=styles['Normal'],
        fontName='RussianFont' if 'RussianFont' in pdfmetrics.getRegisteredFontNames() else 'Helvetica',
        fontSize=10,
        leading=12
    )
    
    # Создаем стиль для заголовков
    russian_title = ParagraphStyle(
        'RussianTitle',
        parent=styles['Title'],
        fontName='RussianFont-Bold' if 'RussianFont-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=16,
        leading=20,
        spaceAfter=20,
        alignment=1  # Центрирование
    )
    
    # Создаем стиль для подзаголовков
    russian_heading = ParagraphStyle(
        'RussianHeading',
        parent=styles['Heading2'],
        fontName='RussianFont-Bold' if 'RussianFont-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold',
        fontSize=14,
        leading=16,
        spaceAfter=12
    )
    
    return russian_style, russian_title, russian_heading

def generate_test_pdf():
    """Генерация тестового PDF с русским текстом"""
    
    print("\n📄 Генерация тестового PDF с русским текстом")
    
    # Регистрируем шрифты
    registered_fonts = register_russian_fonts()
    
    # Создаем стили
    russian_style, russian_title, russian_heading = create_russian_styles()
    
    # Создаем PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = []
    
    # Заголовок
    title = Paragraph("Отчет об изменениях документов", russian_title)
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Информация
    info_text = """
    <b>Базовый документ:</b> Тестовый документ 1<br/>
    <b>Сравниваемый документ:</b> Тестовый документ 2<br/>
    <b>Дата сравнения:</b> 04.10.2025 08:20<br/>
    <b>Пользователь:</b> admin
    """
    info = Paragraph(info_text, russian_style)
    story.append(info)
    story.append(Spacer(1, 20))
    
    # Сводка изменений
    summary_title = Paragraph("Сводка изменений", russian_heading)
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
    
    # Определяем шрифты для таблицы
    if 'RussianFont' in pdfmetrics.getRegisteredFontNames():
        header_font = 'RussianFont-Bold' if 'RussianFont-Bold' in pdfmetrics.getRegisteredFontNames() else 'RussianFont'
        body_font = 'RussianFont'
    else:
        header_font = 'Helvetica-Bold'
        body_font = 'Helvetica'
    
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), header_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('FONTNAME', (0, 1), (-1, -1), body_font),
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
    
    # Сохраняем файл
    output_path = '/Users/wind/Documents/WARA/test_russian_fixed.pdf'
    with open(output_path, 'wb') as f:
        f.write(pdf_data)
    
    print(f"📁 Файл сохранен: {output_path}")
    
    # Проверяем содержимое
    test_words = [
        'Отчет об изменениях документов',
        'Базовый документ',
        'Сравниваемый документ',
        'Сводка изменений',
        'Всего изменений',
        'Добавлено',
        'Удалено',
        'Изменено'
    ]
    
    found_words = 0
    for word in test_words:
        if word.encode('utf-8') in pdf_data:
            print(f"✅ Найдено: '{word}'")
            found_words += 1
        else:
            print(f"❌ Не найдено: '{word}'")
    
    print(f"\n📊 Результат:")
    print(f"   • Найдено слов: {found_words} из {len(test_words)}")
    print(f"   • Процент успеха: {(found_words/len(test_words)*100):.1f}%")
    
    if found_words >= len(test_words) * 0.8:
        print(f"🎉 ОТЛИЧНО! Проблема с шрифтами решена!")
    elif found_words >= len(test_words) * 0.5:
        print(f"⚠️ ЧАСТИЧНО: Большая часть текста работает")
    else:
        print(f"❌ ПРОБЛЕМА: Требуется дополнительная настройка")

if __name__ == '__main__':
    generate_test_pdf()
