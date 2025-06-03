from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.data_manager.models import Content
from django.utils import timezone
from datetime import timedelta


class Command(BaseCommand):
    help = "Check content in the database"

    def handle(self, *args, **kwargs):
        # Проверяем общее количество записей
        total_count = Content.objects.count()
        self.stdout.write(f"Total content records: {total_count}")

        # Проверяем записи за последние 24 часа
        last_24h = timezone.now() - timedelta(hours=24)
        recent_count = Content.objects.filter(created__gte=last_24h).count()
        self.stdout.write(f"Content records created in last 24 hours: {recent_count}")

        # Выводим последние 5 записей
        self.stdout.write("\nLast 5 records:")
        for content in Content.objects.order_by("-created")[:5]:
            self.stdout.write(
                f'\nName: {content.name}\n'
                f'Created: {content.created}\n'
                f'Date Start: {content.date_start}\n'
                f'Date End: {content.date_end}\n'
                f'Location: {content.location}\n'
                f'City: {content.city}\n'
                f'Tags: {", ".join(tag.name for tag in content.tags.all())}\n'
                f'Unique ID: {content.unique_id}'
            )
