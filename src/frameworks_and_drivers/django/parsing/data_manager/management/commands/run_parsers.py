from django.core.management.base import BaseCommand
from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
    GetContentVKController,
    PlacesController,
)
from interface_adapters.controlles.factory import UseCaseFactory


class Command(BaseCommand):
    help = "Запуск парсеров вручную"

    def add_arguments(self, parser):
        parser.add_argument(
            "--parser",
            type=str,
            help="Имя парсера для запуска (tg, vk, timepad, kudago, places, all)",
            required=True,
        )

    def handle(self, *args, **options):
        factory_usecase = UseCaseFactory()
        controllers = {
            "tg": GetContentTgController(usecase_factory=factory_usecase),
            "vk": GetContentVKController(usecase_factory=factory_usecase),
            "timepad": GetContentTimepadController(usecase_factory=factory_usecase),
            "kudago": GetContentKudaGoController(usecase_factory=factory_usecase),
            "places": PlacesController(usecase_factory=factory_usecase),
        }

        parser_name = options["parser"].lower()

        if parser_name == "all":
            self.stdout.write("Запуск всех парсеров последовательно...")
            for name, controller in controllers.items():
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
        else:
            if parser_name not in controllers:
                self.stdout.write(
                    self.style.ERROR(
                        f'Неизвестный парсер: {parser_name}. '
                        f'Доступные парсеры: {", ".join(controllers.keys())}, all'
                    )
                )
                return

            try:
                self.stdout.write(f"Запуск парсера {parser_name}...")
                controllers[parser_name].get_content()
                self.stdout.write(
                    self.style.SUCCESS(f"Парсер {parser_name} успешно завершил работу")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Ошибка в парсере {parser_name}: {str(e)}")
                )
