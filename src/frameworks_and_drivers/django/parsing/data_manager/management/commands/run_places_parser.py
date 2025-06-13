from django.core.management.base import BaseCommand

from usecases.places.run_places_usecase import GetPlacesUsecase
from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_gateway import (
    NLPProcessor,
)
from frameworks_and_drivers.repositories.content_repository import (
    DjangoContentRepository,
)


class Command(BaseCommand):
    help = "Запускает парсер мест (Places) для загрузки данных о местах в базу данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать количество мест для обработки без фактического сохранения",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🏢 Запуск парсера мест..."))

        try:
            # Инициализируем зависимости
            nlp_processor = NLPProcessor()
            content_repo = DjangoContentRepository()

            # Создаем usecase (gateway не используется в places parser)
            places_usecase = GetPlacesUsecase(
                gateway=None,  # Places parser не использует gateway
                nlp_processor=nlp_processor,
                content_repo=content_repo,
                file_repo=None,
            )

            if options["dry_run"]:
                self.stdout.write(
                    "🔍 Режим dry-run: проверяем количество мест для обработки..."
                )

                # Получаем существующие unique_ids
                unique_ids = content_repo.get_all_unique_ids()

                # Импортируем данные мест
                from usecases.places.data import arr

                # Подсчитываем новые места
                new_places_count = 0
                places_with_images = 0

                for place in arr:
                    unique_id = str(place["id"]) + "place"
                    if unique_id not in unique_ids:
                        new_places_count += 1
                        if place.get("image"):
                            places_with_images += 1

                self.stdout.write("📊 Статистика:")
                self.stdout.write(f"   • Всего мест в данных: {len(arr)}")
                self.stdout.write(
                    f'   • Уже в базе: {len([uid for uid in unique_ids if uid.endswith("place")])}'
                )
                self.stdout.write(f"   • Новых мест: {new_places_count}")
                self.stdout.write(
                    f"   • Новых мест с изображениями: {places_with_images}"
                )
                self.stdout.write(
                    f"   • Будет пропущено (без изображений): {new_places_count - places_with_images}"
                )

            else:
                # Запускаем парсер
                self.stdout.write("🚀 Начинаем обработку мест...")
                places_usecase.execute()
                self.stdout.write(
                    self.style.SUCCESS("✅ Парсер мест успешно завершен!")
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка при выполнении парсера мест: {str(e)}")
            )
            raise e
