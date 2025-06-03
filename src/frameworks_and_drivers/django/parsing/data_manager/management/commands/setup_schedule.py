from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.celery_tasks import (
    setup_main_parsers_schedule,
)
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Настраивает расписание запуска парсеров (KudaGo, Timepad, Telegram) дважды в день"

    def handle(self, *args, **options):
        try:
            self.stdout.write(
                self.style.SUCCESS("Начинаем настройку расписания парсеров...")
            )

            # Настраиваем расписание
            setup_main_parsers_schedule()

            self.stdout.write(
                self.style.SUCCESS(
                    "Расписание успешно настроено!\n"
                    "Парсеры будут запускаться:\n"
                    "- Утром в 9:00\n"
                    "- Вечером в 19:00\n"
                    "Порядок запуска: KudaGo → Timepad → Telegram"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Ошибка при настройке расписания: {str(e)}")
            )
            logger.error(f"Error in setup_schedule command: {str(e)}", exc_info=True)
