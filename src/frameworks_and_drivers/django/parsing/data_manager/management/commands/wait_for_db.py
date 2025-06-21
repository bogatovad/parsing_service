import time
from django.core.management.base import BaseCommand
from django.db import connection
from django.db.utils import OperationalError
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Ожидает готовности базы данных"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Максимальное время ожидания в секундах (по умолчанию: 30)",
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        start_time = time.time()

        self.stdout.write("⏳ Ожидание готовности базы данных...")

        while True:
            try:
                # Пытаемся выполнить простой запрос к БД
                connection.ensure_connection()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")

                self.stdout.write(self.style.SUCCESS("✅ База данных готова к работе!"))
                return

            except OperationalError as e:
                elapsed_time = time.time() - start_time

                if elapsed_time >= timeout:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Превышено время ожидания ({timeout}с). "
                            f"База данных недоступна: {str(e)}"
                        )
                    )
                    raise

                self.stdout.write(
                    f"⏳ База данных еще не готова ({elapsed_time:.1f}с/{timeout}с). "
                    f"Повторная попытка через 2 секунды..."
                )
                time.sleep(2)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Неожиданная ошибка: {str(e)}"))
                logger.error(
                    f"Unexpected error in wait_for_db: {str(e)}", exc_info=True
                )
                raise
