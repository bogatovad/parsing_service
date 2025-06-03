from django.core.management.base import BaseCommand
from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
)
from interface_adapters.controlles.factory import UseCaseFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Последовательный запуск основных парсеров (KudaGo → Timepad → Telegram)"

    def handle(self, *args, **options):
        factory_usecase = UseCaseFactory()

        # Инициализируем контроллеры
        kudago_controller = GetContentKudaGoController(usecase_factory=factory_usecase)
        timepad_controller = GetContentTimepadController(
            usecase_factory=factory_usecase
        )
        telegram_controller = GetContentTgController(usecase_factory=factory_usecase)

        # Список парсеров в порядке их запуска
        parsers = [
            ("KudaGo", kudago_controller),
            ("Timepad", timepad_controller),
            ("Telegram", telegram_controller),
        ]

        self.stdout.write(
            self.style.SUCCESS("Начинаем последовательный запуск парсеров...")
        )

        # Последовательно запускаем каждый парсер
        for name, controller in parsers:
            try:
                self.stdout.write(f"Запуск парсера {name}...")
                controller.get_content()
                self.stdout.write(
                    self.style.SUCCESS(f"Парсер {name} успешно завершил работу")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка в парсере {name}: {str(e)}")
                )
                logger.error(f"Error in {name} parser: {str(e)}", exc_info=True)
                # Прерываем выполнение при ошибке
                return

        self.stdout.write(
            self.style.SUCCESS(
                "Все парсеры успешно завершили работу!\n"
                "Порядок выполнения: KudaGo → Timepad → Telegram"
            )
        )
