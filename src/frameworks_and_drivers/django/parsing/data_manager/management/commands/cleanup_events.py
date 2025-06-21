"""
Django management команда для ручной очистки старых мероприятий
"""

from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.data_manager.models import Content
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Удаляет устаревшие мероприятия вручную для тестирования"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать что будет удалено, но не удалять",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            help="Режим async больше не используется - всегда синхронное выполнение",
        )
        parser.add_argument(
            "--days",
            type=int,
            default=1,
            help="Удалить мероприятия старше N дней (по умолчанию: 1, как в оригинальной задаче)",
        )
        parser.add_argument(
            "--stats", action="store_true", help="Показать статистику перед очисткой"
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        is_async = options["async"]
        days_threshold = options["days"]
        show_stats = options["stats"]

        self.stdout.write(self.style.SUCCESS("🧹 Запуск очистки старых мероприятий"))

        if dry_run:
            self.stdout.write("🔍 Режим: DRY RUN (только показать, не удалять)")
        else:
            self.stdout.write("🔄 Режим: синхронный (прямое выполнение)")

        if is_async:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️ Async режим больше не используется - выполняется синхронно"
                )
            )

        self.stdout.write(f"📅 Порог: мероприятия старше {days_threshold} дней")
        self.stdout.write("-" * 50)

        if show_stats or dry_run:
            self._show_stats(days_threshold)

        if dry_run:
            self.stdout.write("\n" + "=" * 50)
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN завершен - никаких изменений не внесено")
            )
            self.stdout.write("💡 Запустите без --dry-run для реального удаления")
            return

        try:
            self.stdout.write("\n🔄 Запускаем очистку...")
            result = self._delete_outdated_events()

            if result and result.get("status") == "success":
                self.stdout.write(self.style.SUCCESS("✅ Очистка завершена успешно"))
                deleted_count = result.get("deleted_count", 0)
                self.stdout.write(f"🗑️ Удалено событий: {deleted_count}")

                # Показать статистику после очистки
                self.stdout.write("\n📊 Статистика после очистки:")
                self._show_current_stats()
            else:
                self.stdout.write(self.style.ERROR("❌ Очистка завершена с ошибками"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка при запуске очистки: {str(e)}")
            )
            logger.error(f"Error running cleanup: {str(e)}", exc_info=True)

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("🎉 Команда очистки завершена!"))

    def _delete_outdated_events(self):
        """Функция очистки устаревших событий (перенесена из Celery задачи)"""
        try:
            logger.info("Starting deletion of outdated events")
            logger.info(f"Task execution time: {timezone.now()}")

            # Используем текущую дату в UTC
            today = timezone.now().date()

            logger.info(
                f"Deleting events that ended before {today} (UTC). Today is {today}"
            )
            logger.info(f"Current timezone: {timezone.get_current_timezone()}")

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

            # Логируем каждый тип событий отдельно
            multi_day_list = list(
                multi_day_events.values("id", "name", "date_start", "date_end")
            )
            single_no_end_list = list(
                single_day_no_end.values("id", "name", "date_start")
            )
            single_same_dates_list = list(
                single_day_same_dates.values("id", "name", "date_start", "date_end")
            )

            logger.info(
                f"Found {len(multi_day_list)} multi-day events to delete: {multi_day_list}"
            )
            logger.info(
                f"Found {len(single_no_end_list)} single-day events (no end date) to delete: {single_no_end_list}"
            )
            logger.info(
                f"Found {len(single_same_dates_list)} single-day events (same dates) to delete: {single_same_dates_list}"
            )

            # Объединяем все запросы
            all_events = multi_day_events | single_day_no_end | single_day_same_dates

            # Удаляем события
            deleted_count, details = all_events.delete()

            logger.info(
                f"Successfully deleted {deleted_count} events with outdated dates"
            )
            logger.info(f"Deletion details: {details}")

            return {
                "status": "success",
                "deleted_count": deleted_count,
                "details": {
                    "multi_day_events": len(multi_day_list),
                    "single_day_no_end": len(single_no_end_list),
                    "single_day_same_dates": len(single_same_dates_list),
                },
            }

        except Exception as exc:
            logger.error(f"Error in delete_outdated_events: {exc}", exc_info=True)
            return {"status": "error", "message": str(exc)}

    def _show_stats(self, days_threshold):
        """Показывает статистику мероприятий перед очисткой (точно как в delete_outdated_events)"""
        try:
            self.stdout.write("\n📊 Статистика мероприятий:")

            # Общее количество (используем Content как в оригинальной задаче)
            total_events = Content.objects.count()
            self.stdout.write(f"📈 Всего мероприятий: {total_events}")

            # Используем UTC как в оригинальной задаче
            today = timezone.now().date()
            threshold_date = today - timedelta(days=days_threshold)

            self.stdout.write(f"📅 Сегодня (UTC): {today}")
            self.stdout.write(f"🗓️  Порог удаления: {threshold_date}")

            # Получаем события для удаления по той же логике что в delete_outdated_events
            multi_day_events, single_day_no_end, single_day_same_dates = (
                self._get_events_for_deletion(threshold_date)
            )

            total_to_delete = (
                multi_day_events.count()
                + single_day_no_end.count()
                + single_day_same_dates.count()
            )

            self.stdout.write(
                f"🗑️  К удалению (старше {days_threshold} дней): {total_to_delete}"
            )
            self.stdout.write(
                f"   • Многодневные (завершились): {multi_day_events.count()}"
            )
            self.stdout.write(
                f"   • Однодневные (без даты окончания): {single_day_no_end.count()}"
            )
            self.stdout.write(
                f"   • Однодневные (одинаковые даты): {single_day_same_dates.count()}"
            )

            # Будущие мероприятия
            future_events = Content.objects.filter(date_start__gt=today).count()
            self.stdout.write(f"🚀 Будущие мероприятия: {future_events}")

            # Мероприятия сегодня
            today_events = Content.objects.filter(date_start=today).count()
            self.stdout.write(f"📅 Мероприятия сегодня: {today_events}")

            if total_to_delete > 0:
                self.stdout.write("\n🔍 Примеры мероприятий к удалению:")

                # Показать примеры из каждой категории
                for event in multi_day_events[:3]:
                    end_date_str = (
                        f" - {event.date_end.strftime('%d.%m.%Y')}"
                        if event.date_end
                        else ""
                    )
                    self.stdout.write(
                        f"  • [Многодневное] {event.name[:40]}... "
                        f"({event.date_start.strftime('%d.%m.%Y')}{end_date_str})"
                    )

                for event in single_day_no_end[:2]:
                    self.stdout.write(
                        f"  • [Однодневное] {event.name[:40]}... "
                        f"({event.date_start.strftime('%d.%m.%Y')})"
                    )

                if total_to_delete > 5:
                    self.stdout.write(f"  ... и ещё {total_to_delete - 5} мероприятий")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка при получении статистики: {str(e)}")
            )

    def _show_current_stats(self):
        """Показывает текущую статистику после очистки"""
        try:
            total_events = Content.objects.count()
            self.stdout.write(f"📈 Всего мероприятий осталось: {total_events}")

            today = timezone.now().date()

            future_events = Content.objects.filter(date_start__gt=today).count()
            self.stdout.write(f"🚀 Будущие мероприятия: {future_events}")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка при получении статистики: {str(e)}")
            )

    def _get_events_for_deletion(self, threshold_date):
        """Получает мероприятия для удаления по ТОЧНО той же логике что и в delete_outdated_events"""

        # ТОЧНО та же логика что в delete_outdated_events задаче:

        # 1. События с указанными датами начала и окончания (многодневные, которые уже завершились)
        multi_day_events = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & ~Q(date_start=F("date_end"))  # Исключаем однодневные события
            & Q(date_end__lte=threshold_date)  # Изменено с __lt на __lte (включительно)
        )

        # 2. Однодневные события без даты окончания
        single_day_no_end = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=True)
            & Q(
                date_start__lte=threshold_date
            )  # Изменено с __lt на __lte (включительно)
        )

        # 3. Однодневные события с одинаковыми датами начала и окончания
        single_day_same_dates = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & Q(date_start=F("date_end"))
            & Q(
                date_start__lte=threshold_date
            )  # Изменено с __lt на __lte (включительно)
        )

        return multi_day_events, single_day_no_end, single_day_same_dates
