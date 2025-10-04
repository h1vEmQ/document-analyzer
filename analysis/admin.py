from django.contrib import admin
from .models import Comparison, Change, AnalysisSettings


class ChangeInline(admin.TabularInline):
    """
    Инлайн для отображения изменений в сравнении
    """
    model = Change
    extra = 0
    readonly_fields = ('change_type', 'location', 'section', 'confidence')
    fields = ('change_type', 'location', 'section', 'confidence')


@admin.register(Comparison)
class ComparisonAdmin(admin.ModelAdmin):
    """
    Админ-панель для сравнений документов
    """
    list_display = ('title', 'base_document', 'compared_document', 'status', 'user', 'created_date', 'get_total_changes')
    list_filter = ('status', 'created_date', 'user__role')
    search_fields = ('title', 'base_document__title', 'compared_document__title', 'user__username')
    readonly_fields = ('created_date', 'completed_date', 'processing_time')
    ordering = ('-created_date',)
    inlines = [ChangeInline]
    
    fieldsets = (
        ('Основная информация', {'fields': ('title', 'base_document', 'compared_document', 'status')}),
        ('Пользователь', {'fields': ('user',)}),
        ('Временные метки', {'fields': ('created_date', 'completed_date', 'processing_time')}),
        ('Результаты', {'fields': ('changes_summary', 'detailed_changes')}),
    )
    
    def get_total_changes(self, obj):
        """Отображает общее количество изменений"""
        return obj.get_total_changes()
    get_total_changes.short_description = 'Всего изменений'


@admin.register(Change)
class ChangeAdmin(admin.ModelAdmin):
    """
    Админ-панель для отдельных изменений
    """
    list_display = ('comparison', 'change_type', 'location', 'section', 'confidence')
    list_filter = ('change_type', 'location', 'comparison__status')
    search_fields = ('section', 'old_value', 'new_value', 'comparison__title')
    readonly_fields = ('confidence',)
    ordering = ('comparison', 'change_type', 'section')


@admin.register(AnalysisSettings)
class AnalysisSettingsAdmin(admin.ModelAdmin):
    """
    Админ-панель для настроек анализа
    """
    list_display = ('user', 'sensitivity', 'include_text_changes', 'include_table_changes', 'include_structure_changes')
    list_filter = ('include_text_changes', 'include_table_changes', 'include_structure_changes')
    search_fields = ('user__username', 'user__email')
    
    fieldsets = (
        ('Пользователь', {'fields': ('user',)}),
        ('Настройки анализа', {'fields': (
            'sensitivity', 
            'include_text_changes', 
            'include_table_changes', 
            'include_structure_changes',
            'min_change_length'
        )}),
    )