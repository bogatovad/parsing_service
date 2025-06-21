from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.tasks import (
    setup_all_schedules,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Настраивает расписание для всех автоматических задач: парсеры, очистка старых событий и уведомления"

    def add_arguments(self, parser):
        parser.add_argument(
            "--only",
            choices=["parsers", "cleanup", "notifications", "all"],
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
                        "- Ежедневно в 8:00 MSK (KudaGo → Timepad → Telegram → VK)\n\n"
                        "📩 УВЕДОМЛЕНИЯ:\n"
                        "- Ежедневно в 9:00 MSK (отправка уведомлений об избранных событиях)\n\n"
                        "🧹 ОЧИСТКА СТАРЫХ СОБЫТИЙ:\n"
                        "- Ежедневно в 00:00 MSK (полночь)\n\n"
                        "⚡ Оптимизированное расписание снижает нагрузку на систему.\n"
                        "Все задачи сохранены в базе данных и будут выполняться автоматически."
                    )
                )
            elif only == "parsers":
                from frameworks_and_drivers.django.parsing.tasks import (
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
                from frameworks_and_drivers.django.parsing.tasks import (
                    setup_cleanup_schedule,
                )

                self.stdout.write(
                    self.style.SUCCESS("Настраиваем только расписание очистки...")
                )
                setup_cleanup_schedule()
                self.stdout.write(
                    self.style.SUCCESS("✅ Расписание очистки настроено!")
                )
            elif only == "notifications":
                from frameworks_and_drivers.django.parsing.tasks import (
                    setup_notifications_schedule,
                )

                self.stdout.write(
                    self.style.SUCCESS("Настраиваем только расписание уведомлений...")
                )
                setup_notifications_schedule()
                self.stdout.write(
                    self.style.SUCCESS("✅ Расписание уведомлений настроено!")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при настройке расписания: {str(e)}")
            )
            logger.error(f"Error in setup_schedule command: {str(e)}", exc_info=True)
