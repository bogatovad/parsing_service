"""
Django management команда для ручного запуска парсеров
"""

from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.celery_tasks import (
    parse_kudago,
    parse_timepad,
    parse_telegram,
    parse_vk,
    parse_places,
    run_main_parsers,
    run_all_parsers,
)
from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
    GetContentVKController,
    PlacesController,
)
from interface_adapters.controlles.factory import UseCaseFactory
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Запускает парсеры вручную для тестирования"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Инициализируем контроллеры для прямого запуска
        self.factory_usecase = UseCaseFactory()
        self.controllers = {
            "kudago": GetContentKudaGoController(usecase_factory=self.factory_usecase),
            "timepad": GetContentTimepadController(
                usecase_factory=self.factory_usecase
            ),
            "telegram": GetContentTgController(usecase_factory=self.factory_usecase),
            "vk": GetContentVKController(usecase_factory=self.factory_usecase),
            "places": PlacesController(usecase_factory=self.factory_usecase),
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "parsers",
            nargs="*",
            choices=["kudago", "timepad", "telegram", "vk", "places", "main", "all"],
            help="Какие парсеры запустить (по умолчанию: main)",
        )
        parser.add_argument(
            "--async",
            action="store_true",
            help="Запустить асинхронно через Celery (по умолчанию: синхронно)",
        )

    def handle(self, *args, **options):
        parsers = options["parsers"] or ["main"]
        is_async = options["async"]

        self.stdout.write(
            self.style.SUCCESS(f"🚀 Запускаем парсеры: {', '.join(parsers)}")
        )

        if is_async:
            self.stdout.write("⚡ Режим: асинхронный (через Celery)")
        else:
            self.stdout.write("🔄 Режим: синхронный (ожидание результата)")

        self.stdout.write("-" * 50)

        for parser_name in parsers:
            try:
                self.stdout.write(f"\n📦 Запускаем {parser_name}...")

                if parser_name == "kudago":
                    result = self._run_parser(
                        "kudago", parse_kudago, is_async, "KudaGo"
                    )
                elif parser_name == "timepad":
                    result = self._run_parser(
                        "timepad", parse_timepad, is_async, "Timepad"
                    )
                elif parser_name == "telegram":
                    result = self._run_parser(
                        "telegram", parse_telegram, is_async, "Telegram"
                    )
                elif parser_name == "vk":
                    result = self._run_parser("vk", parse_vk, is_async, "VK")
                elif parser_name == "places":
                    result = self._run_parser(
                        "places", parse_places, is_async, "Places"
                    )
                elif parser_name == "main":
                    result = self._run_main_parsers(is_async)
                elif parser_name == "all":
                    result = self._run_all_parsers(is_async)

                if is_async and hasattr(result, "id"):
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {parser_name} запущен асинхронно. Task ID: {result.id}"
                        )
                    )

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Ошибка при запуске {parser_name}: {str(e)}")
                )
                logger.error(
                    f"Error running parser {parser_name}: {str(e)}", exc_info=True
                )

        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS("🎉 Запуск парсеров завершен!"))

        if not is_async:
            self.stdout.write(
                "\n💡 Совет: используйте --async для асинхронного запуска через Celery"
            )

    def _run_parser(self, parser_key, celery_func, is_async, display_name):
        """Запускает парсер синхронно или асинхронно"""
        if is_async:
            # Асинхронный запуск через Celery
            return celery_func.delay()
        else:
            # Синхронный запуск напрямую через контроллер
            self.stdout.write(f"⏳ Выполняется {display_name}...")
            try:
                controller = self.controllers[parser_key]
                result = controller.get_content()
                self.stdout.write(f"✅ {display_name} завершен успешно")
                return result
            except Exception as e:
                self.stdout.write(f"❌ Ошибка в {display_name}: {str(e)}")
                logger.error(f"Error in {display_name}: {str(e)}", exc_info=True)
                return False

    def _run_main_parsers(self, is_async):
        """Запускает основные парсеры последовательно"""
        if is_async:
            return run_main_parsers.delay()
        else:
            self.stdout.write(
                "⏳ Выполняется последовательный запуск основных парсеров..."
            )
            parsers_order = ["kudago", "timepad", "telegram", "vk"]
            results = []

            for parser_name in parsers_order:
                self.stdout.write(f"\n🔄 Запускаем {parser_name.upper()}...")
                try:
                    controller = self.controllers[parser_name]
                    result = controller.get_content()
                    if result:
                        self.stdout.write(f"✅ {parser_name.upper()} завершен успешно")
                    else:
                        self.stdout.write(
                            f"⚠️ {parser_name.upper()} завершен с предупреждениями"
                        )
                    results.append(result)
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка в {parser_name.upper()}: {str(e)}")
                    logger.error(f"Error in {parser_name}: {str(e)}", exc_info=True)
                    results.append(False)

            return all(results)

    def _run_all_parsers(self, is_async):
        """Запускает все парсеры включая Places"""
        if is_async:
            return run_all_parsers.delay()
        else:
            self.stdout.write("⏳ Выполняется последовательный запуск всех парсеров...")
            parsers_order = ["kudago", "timepad", "telegram", "vk", "places"]
            results = []

            for parser_name in parsers_order:
                self.stdout.write(f"\n🔄 Запускаем {parser_name.upper()}...")
                try:
                    controller = self.controllers[parser_name]
                    result = controller.get_content()
                    if result:
                        self.stdout.write(f"✅ {parser_name.upper()} завершен успешно")
                    else:
                        self.stdout.write(
                            f"⚠️ {parser_name.upper()} завершен с предупреждениями"
                        )
                    results.append(result)
                except Exception as e:
                    self.stdout.write(f"❌ Ошибка в {parser_name.upper()}: {str(e)}")
                    logger.error(f"Error in {parser_name}: {str(e)}", exc_info=True)
                    results.append(False)

            return all(results)
