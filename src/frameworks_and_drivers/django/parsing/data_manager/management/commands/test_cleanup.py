from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.tasks import delete_outdated_events
import uuid
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Тестирование задачи удаления устаревших событий"

    def add_arguments(self, parser):
        parser.add_argument(
            "--sync",
            action="store_true",
            help="Запустить синхронно (без Celery)",
        )

    def handle(self, *args, **options):
        if options["sync"]:
            self.stdout.write("🔄 Запуск задачи синхронно...")
            try:
                result = delete_outdated_events()
                self.stdout.write(self.style.SUCCESS(f"✅ Задача выполнена: {result}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка: {str(e)}"))
        else:
            self.stdout.write("🚀 Запуск задачи через Celery...")
            try:
                # Используем уникальный ID для избежания кэширования
                unique_id = str(uuid.uuid4())
                result = delete_outdated_events.apply_async(task_id=unique_id)

                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Задача поставлена в очередь:\n"
                        f"   Task ID: {result.task_id}\n"
                        f"   Status: {result.status}\n\n"
                        f"📋 Для проверки выполнения:\n"
                        f"   docker compose logs -f celery-worker-parsing"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Ошибка: {str(e)}"))
