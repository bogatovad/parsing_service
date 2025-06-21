import logging
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import F, Q
from frameworks_and_drivers.django.parsing.data_manager.models import Content

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Delete outdated events based on date conditions"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        try:
            self.stdout.write("🧹 Starting deletion of outdated events")
            self.stdout.write(f"⏰ Task execution time: {timezone.now()}")

            # Используем текущую дату в UTC
            today = timezone.now().date()

            self.stdout.write(
                f"📅 Deleting events that ended before {today} (UTC). Today is {today}"
            )
            self.stdout.write(f"🌍 Current timezone: {timezone.get_current_timezone()}")

            # 1. События с указанными датами начала и окончания (многодневные, которые уже завершились)
            multi_day_events = Content.objects.filter(
                Q(date_start__isnull=False)
                & Q(date_end__isnull=False)
                & ~Q(date_start=F("date_end"))  # Исключаем однодневные события
                & Q(date_end__lt=today)  # Удаляем события, закончившиеся ДО сегодня
            )

            # 2. Однодневные события без даты окончания
            single_day_no_end = Content.objects.filter(
                Q(date_start__isnull=False)
                & Q(date_end__isnull=True)
                & Q(
                    date_start__lt=today
                )  # Удаляем события, которые начались ДО сегодня
            )

            # 3. Однодневные события с одинаковыми датами начала и окончания
            single_day_same_dates = Content.objects.filter(
                Q(date_start__isnull=False)
                & Q(date_end__isnull=False)
                & Q(date_start=F("date_end"))
                & Q(date_start__lt=today)  # Удаляем события, которые были ДО сегодня
            )

            # Получаем списки для логирования
            multi_day_list = list(
                multi_day_events.values("id", "name", "date_start", "date_end")
            )
            single_no_end_list = list(
                single_day_no_end.values("id", "name", "date_start")
            )
            single_same_dates_list = list(
                single_day_same_dates.values("id", "name", "date_start", "date_end")
            )

            self.stdout.write(
                f"📊 Found {len(multi_day_list)} multi-day events to delete"
            )
            self.stdout.write(
                f"📊 Found {len(single_no_end_list)} single-day events (no end date) to delete"
            )
            self.stdout.write(
                f"📊 Found {len(single_same_dates_list)} single-day events (same dates) to delete"
            )

            # Показываем подробности
            if multi_day_list:
                self.stdout.write("🗂️ Multi-day events:")
                for event in multi_day_list[:5]:  # Показываем первые 5
                    self.stdout.write(
                        f"  - {event['name'][:50]}... ({event['date_start']} - {event['date_end']})"
                    )
                if len(multi_day_list) > 5:
                    self.stdout.write(f"  ... и еще {len(multi_day_list) - 5}")

            if single_no_end_list:
                self.stdout.write("📅 Single-day events (no end):")
                for event in single_no_end_list[:5]:
                    self.stdout.write(
                        f"  - {event['name'][:50]}... ({event['date_start']})"
                    )
                if len(single_no_end_list) > 5:
                    self.stdout.write(f"  ... и еще {len(single_no_end_list) - 5}")

            if single_same_dates_list:
                self.stdout.write("📆 Single-day events (same dates):")
                for event in single_same_dates_list[:5]:
                    self.stdout.write(
                        f"  - {event['name'][:50]}... ({event['date_start']})"
                    )
                if len(single_same_dates_list) > 5:
                    self.stdout.write(f"  ... и еще {len(single_same_dates_list) - 5}")

            # Объединяем все запросы
            all_events = multi_day_events | single_day_no_end | single_day_same_dates
            total_count = all_events.count()

            if dry_run:
                self.stdout.write(
                    self.style.WARNING(f"🔍 DRY RUN: Would delete {total_count} events")
                )
                return

            if total_count == 0:
                self.stdout.write(self.style.SUCCESS("✅ No outdated events found"))
                return

            # Удаляем события
            deleted_count, details = all_events.delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully deleted {deleted_count} events with outdated dates"
                )
            )
            self.stdout.write(f"📋 Deletion details: {details}")

            logger.info(f"Cleanup completed: deleted {deleted_count} events")

        except Exception as exc:
            error_msg = f"❌ Error in cleanup: {exc}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg, exc_info=True)
            raise
