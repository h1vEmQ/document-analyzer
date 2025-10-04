# 🔧 Исправление ошибки AttributeError: 'FieldFile' object has no attribute 'content_type'

## ❌ Проблема
При загрузке документов через веб-интерфейс возникала ошибка:
```
AttributeError: 'FieldFile' object has no attribute 'content_type'
```

## 🔍 Причина
В сервисе валидации документов (`documents/services.py`) код пытался получить атрибут `content_type` у объекта `FieldFile`, который не всегда имеет этот атрибут.

## ✅ Решение
Заменили прямое обращение к `file.content_type` на безопасное получение атрибута с помощью `getattr()`:

### Было:
```python
'content_type': file.content_type
```

### Стало:
```python
'content_type': getattr(file, 'content_type', 'application/octet-stream')
```

## 📍 Место исправления
**Файл:** `/Users/wind/Documents/WARA/documents/services.py`  
**Строка:** 326  
**Метод:** `DocumentValidationService.validate_upload()`

## 🧪 Тестирование
После исправления тест показал:
```
✅ Валидность: True
📊 Информация о файле: {
    'name': 'test_document_20251004_105109.docx', 
    'size': 37952, 
    'size_mb': 0.04, 
    'extension': '.docx', 
    'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
}
```

## 🎉 Результат
- ✅ **Ошибка устранена** - загрузка документов работает корректно
- ✅ **Валидация работает** - файлы проверяются без ошибок
- ✅ **Совместимость сохранена** - код работает с разными типами файлов
- ✅ **Fallback добавлен** - если `content_type` отсутствует, используется значение по умолчанию

**Проблема полностью решена!** 🚀
