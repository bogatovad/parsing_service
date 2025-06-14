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
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Запускает парсеры вручную для тестирования"

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
                    result = self._run_parser(parse_kudago, is_async, "KudaGo")
                elif parser_name == "timepad":
                    result = self._run_parser(parse_timepad, is_async, "Timepad")
                elif parser_name == "telegram":
                    result = self._run_parser(parse_telegram, is_async, "Telegram")
                elif parser_name == "vk":
                    result = self._run_parser(parse_vk, is_async, "VK")
                elif parser_name == "places":
                    result = self._run_parser(parse_places, is_async, "Places")
                elif parser_name == "main":
                    result = self._run_parser(
                        run_main_parsers,
                        is_async,
                        "Main Parsers (KudaGo→Timepad→Telegram→VK)",
                    )
                elif parser_name == "all":
                    result = self._run_parser(
                        run_all_parsers, is_async, "All Parsers (включая Places)"
                    )

                if is_async:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"✅ {parser_name} запущен асинхронно. Task ID: {result.id}"
                        )
                    )
                else:
                    if result:
                        self.stdout.write(
                            self.style.SUCCESS(f"✅ {parser_name} завершен успешно")
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"❌ {parser_name} завершен с ошибкой")
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

    def _run_parser(self, parser_func, is_async, display_name):
        """Запускает парсер синхронно или асинхронно"""
        if is_async:
            # Асинхронный запуск через Celery
            return parser_func.delay()
        else:
            # Синхронный запуск
            self.stdout.write(f"⏳ Выполняется {display_name}...")
            return parser_func()
