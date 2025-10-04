#!/usr/bin/env python
"""
Скрипт для создания демо-пользователей
"""
import os
import sys
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'wara_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

def create_demo_users():
    """Создание демо-пользователей"""
    
    demo_users = [
        {
            'username': 'admin',
            'email': 'admin@wara.local',
            'first_name': 'Администратор',
            'last_name': 'Системы',
            'role': 'admin',
            'department': 'IT',
            'password': 'admin123',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'manager',
            'email': 'manager@wara.local',
            'first_name': 'Руководитель',
            'last_name': 'Отдела',
            'role': 'manager',
            'department': 'Управление',
            'password': 'manager123',
            'is_staff': True,
            'is_superuser': False
        },
        {
            'username': 'user',
            'email': 'user@wara.local',
            'first_name': 'Пользователь',
            'last_name': 'Обычный',
            'role': 'viewer',
            'department': 'Операции',
            'password': 'user123',
            'is_staff': False,
            'is_superuser': False
        }
    ]
    
    created_count = 0
    
    with transaction.atomic():
        for user_data in demo_users:
            username = user_data.pop('username')
            password = user_data.pop('password')
            
            # Проверяем, существует ли пользователь
            if User.objects.filter(username=username).exists():
                print(f"Пользователь {username} уже существует")
                continue
            
            # Создаем пользователя
            user = User.objects.create_user(username=username, password=password, **user_data)
            print(f"Создан пользователь: {user.username} ({user.get_role_display()})")
            created_count += 1
    
    print(f"\nСоздано пользователей: {created_count}")
    print("\nДемо-аккаунты:")
    print("Администратор: admin / admin123")
    print("Руководитель: manager / manager123")
    print("Пользователь: user / user123")

if __name__ == '__main__':
    create_demo_users()
