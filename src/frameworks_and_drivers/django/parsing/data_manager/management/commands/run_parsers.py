"""
Django management команда для ручного запуска парсеров
"""

import logging
from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.celery_tasks import (
    run_main_parsers,
    run_all_parsers,
)
from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
    GetContentVKController,
)
from interface_adapters.controlles.factory import UseCaseFactory

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Run content parsers"

    def add_arguments(self, parser):
        parser.add_argument(
            "--parser",
            type=str,
            choices=["kudago", "timepad", "telegram", "vk", "all"],
            default="all",
            help="Which parser to run (default: all)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what parsers would run without actually running them",
        )

    def handle(self, *args, **options):
        parser_name = options["parser"]
        dry_run = options["dry_run"]

        # Создаем фабрику и контроллеры
        factory_usecase = UseCaseFactory()

        parsers = {
            "kudago": (
                "KudaGo",
                GetContentKudaGoController(usecase_factory=factory_usecase),
            ),
            "timepad": (
                "Timepad",
                GetContentTimepadController(usecase_factory=factory_usecase),
            ),
            "telegram": (
                "Telegram",
                GetContentTgController(usecase_factory=factory_usecase),
            ),
            "vk": ("VK", GetContentVKController(usecase_factory=factory_usecase)),
        }

        if parser_name == "all":
            selected_parsers = parsers.items()
        else:
            selected_parsers = [(parser_name, parsers[parser_name])]

        self.stdout.write("🚀 Starting parsers execution")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE"))
            for parser_key, (parser_display_name, _) in selected_parsers:
                self.stdout.write(f"  Would run: {parser_display_name}")
            return

        results = []

        for parser_key, (parser_display_name, controller) in selected_parsers:
            try:
                self.stdout.write(f"▶️  Starting {parser_display_name} parser...")
                controller.get_content()
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {parser_display_name} parser completed successfully"
                    )
                )
                results.append({"parser": parser_display_name, "status": "success"})
                logger.info(f"{parser_display_name} parser finished successfully")

            except Exception as e:
                error_msg = f"❌ Error in {parser_display_name} parser: {str(e)}"
                self.stdout.write(self.style.ERROR(error_msg))
                results.append(
                    {"parser": parser_display_name, "status": "error", "error": str(e)}
                )
                logger.error(f"Error in {parser_display_name} parser: {str(e)}")

        # Итоговый отчет
        successful = len([r for r in results if r["status"] == "success"])
        failed = len([r for r in results if r["status"] == "error"])

        self.stdout.write("\n📊 Execution Summary:")
        self.stdout.write(f"  ✅ Successful: {successful}")
        self.stdout.write(f"  ❌ Failed: {failed}")

        if failed > 0:
            self.stdout.write("\n🔍 Failed parsers:")
            for result in results:
                if result["status"] == "error":
                    self.stdout.write(f"  - {result['parser']}: {result['error']}")

        logger.info(
            f"Parsers execution completed: {successful} successful, {failed} failed"
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
