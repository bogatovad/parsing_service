from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.celery_tasks import (
    setup_all_schedules,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Настраивает расписание для всех автоматических задач: парсеры и очистка старых событий"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            choices=["parsers", "cleanup", "all"],
            default="all",
            help="Настроить только определенные расписания (по умолчанию: all)",
        )

    def handle(self, *args, **options):
        try:
            only = options["only"]

            if only == "all":
                self.stdout.write(
                    self.style.SUCCESS("Начинаем настройку всех расписаний...")
                )

                # Настраиваем все расписания
                setup_all_schedules()

                self.stdout.write(
                    self.style.SUCCESS(
                        "✅ Все расписания успешно настроены!\n\n"
                        "📅 ПАРСЕРЫ:\n"
                        "- Утром в 9:00 (KudaGo → Timepad → Telegram → VK)\n"
                        "- Вечером в 19:00 (KudaGo → Timepad → Telegram → VK)\n\n"
                        "🧹 ОЧИСТКА СТАРЫХ СОБЫТИЙ:\n"
                        "- Ежедневно в 23:00\n\n"
                        "Все задачи сохранены в базе данных и будут выполняться автоматически."
                    )
                )
            elif only == "parsers":
                from frameworks_and_drivers.django.parsing.celery_tasks import (
                    setup_main_parsers_schedule,
                )

                self.stdout.write(
                    self.style.SUCCESS("Настраиваем только расписание парсеров...")
                )
                setup_main_parsers_schedule()
                self.stdout.write(
                    self.style.SUCCESS("✅ Расписание парсеров настроено!")
                )
            elif only == "cleanup":
                from frameworks_and_drivers.django.parsing.celery_tasks import (
                    setup_cleanup_schedule,
                )

                self.stdout.write(
                    self.style.SUCCESS("Настраиваем только расписание очистки...")
                )
                setup_cleanup_schedule()
                self.stdout.write(
                    self.style.SUCCESS("✅ Расписание очистки настроено!")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при настройке расписания: {str(e)}")
            )
            logger.error(f"Error in setup_schedule command: {str(e)}", exc_info=True)
