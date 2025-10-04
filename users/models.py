from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Расширенная модель пользователя с ролями для WARA системы
    """
    ROLE_CHOICES = [
        ('admin', 'Администратор'),
        ('manager', 'Руководитель'),
        ('viewer', 'Наблюдатель'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='viewer',
        verbose_name='Роль'
    )
    
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Отдел'
    )
    
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Телефон'
    )
    
    notification_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Настройки уведомлений'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']
    
    def __str__(self):
        return f"{self.get_full_name()} ({self.get_role_display()})"
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_manager(self):
        return self.role == 'manager'
    
    def is_viewer(self):
        return self.role == 'viewer'