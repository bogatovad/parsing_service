from django.core.management.base import BaseCommand
from frameworks_and_drivers.django.parsing.data_manager.tasks import (
    run_telegram_parser_task,
)


class Command(BaseCommand):
    help = "Run Telegram parser via Celery task"

    def handle(self, *args, **options):
        self.stdout.write("Starting Telegram parser task...")
        task = run_telegram_parser_task.delay()
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully started Telegram parser task with ID: {task.id}"
            )
        )
