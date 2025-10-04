from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Админ-панель для модели пользователя
    """
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser', 'department')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('username',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {'fields': ('first_name', 'last_name', 'email', 'phone')}),
        ('Рабочая информация', {'fields': ('role', 'department')}),
        ('Разрешения', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Важные даты', {'fields': ('last_login', 'date_joined')}),
        ('Настройки уведомлений', {'fields': ('notification_settings',)}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role', 'department'),
        }),
    )