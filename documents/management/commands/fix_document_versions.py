from django.core.management.base import BaseCommand
from django.db.models import Q
from documents.models import Document


class Command(BaseCommand):
    help = 'Исправляет дублированные флаги is_latest_version в документах'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Показать что будет исправлено без внесения изменений',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Режим предварительного просмотра (dry-run)'))
        
        # Находим все корневые документы (без parent_document)
        root_documents = Document.objects.filter(parent_document__isnull=True)
        
        fixed_count = 0
        total_duplicates = 0
        
        for root_doc in root_documents:
            # Получаем все версии этого документа
            all_versions = Document.objects.filter(
                Q(id=root_doc.id) | Q(parent_document=root_doc.id)
            ).order_by('upload_date')
            
            if all_versions.count() <= 1:
                continue  # Если только одна версия, пропускаем
                
            # Находим версии с is_latest_version=True
            latest_versions = all_versions.filter(is_latest_version=True)
            
            if latest_versions.count() > 1:
                total_duplicates += latest_versions.count() - 1
                
                self.stdout.write(
                    f'Найдены дубликаты в документе "{root_doc.title}" (ID: {root_doc.id}):'
                )
                
                for version in latest_versions:
                    self.stdout.write(
                        f'  - Версия {version.version} (ID: {version.id}) - {version.upload_date}'
                    )
                
                # Определяем последнюю версию по дате
                actual_latest = all_versions.order_by('-upload_date').first()
                
                self.stdout.write(
                    f'  Последняя версия по дате: {actual_latest.version} (ID: {actual_latest.id})'
                )
                
                if not dry_run:
                    # Сбрасываем все флаги
                    all_versions.update(is_latest_version=False)
                    
                    # Устанавливаем флаг только для последней версии
                    actual_latest.is_latest_version = True
                    actual_latest.save()
                    
                    self.stdout.write(
                        self.style.SUCCESS(f'  ✅ Исправлено')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  🔍 Будет исправлено')
                    )
                
                fixed_count += 1
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'\nНайдено {fixed_count} документов с дубликатами '
                    f'({total_duplicates} лишних флагов is_latest_version)'
                )
            )
            self.stdout.write(
                'Запустите команду без --dry-run для исправления'
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n✅ Исправлено {fixed_count} документов '
                    f'({total_duplicates} лишних флагов is_latest_version)'
                )
            )
