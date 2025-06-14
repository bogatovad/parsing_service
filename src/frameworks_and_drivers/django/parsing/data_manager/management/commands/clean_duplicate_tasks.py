"""
Django management команда для очистки дублирующих периодических задач
"""

from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Удаляет дублирующие периодические задачи"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показать что будет удалено, но не удалять",
        )
        parser.add_argument(
            "--list-all", action="store_true", help="Показать все существующие задачи"
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        list_all = options["list_all"]

        self.stdout.write(
            self.style.SUCCESS("🧹 Очистка дублирующих периодических задач")
        )

        if dry_run:
            self.stdout.write("🔍 Режим: DRY RUN (только показать, не удалять)")

        self.stdout.write("-" * 60)

        if list_all:
            self._list_all_tasks()
            return

        # Список задач для удаления (старые дубликаты)
        tasks_to_delete = [
            "run-main-parsers-morning",
            "run-main-parsers-evening",
        ]

        # Показываем текущие задачи
        self._show_current_tasks()

        # Удаляем дубликаты
        deleted_count = 0
        for task_name in tasks_to_delete:
            try:
                tasks = PeriodicTask.objects.filter(name=task_name)
                if tasks.exists():
                    self.stdout.write(f"\n🗑️  Найдена задача для удаления: {task_name}")
                    for task in tasks:
                        self.stdout.write(f"   • ID: {task.id}")
                        self.stdout.write(f"   • Задача: {task.task}")
                        self.stdout.write(
                            f"   • Расписание: {task.crontab or task.interval}"
                        )
                        self.stdout.write(f"   • Включена: {task.enabled}")

                    if not dry_run:
                        count = tasks.count()
                        tasks.delete()
                        deleted_count += count
                        self.stdout.write(
                            self.style.SUCCESS(
                                f"   ✅ Удалено {count} задач с именем '{task_name}'"
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(
                                f"   🔍 Будет удалено {tasks.count()} задач (DRY RUN)"
                            )
                        )
                else:
                    self.stdout.write(f"ℹ️  Задача '{task_name}' не найдена")

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Ошибка при обработке задачи '{task_name}': {str(e)}"
                    )
                )
                logger.error(
                    f"Error processing task {task_name}: {str(e)}", exc_info=True
                )

        self.stdout.write("\n" + "=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN завершен - никаких изменений не внесено")
            )
            self.stdout.write("💡 Запустите без --dry-run для реального удаления")
        else:
            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"🎉 Успешно удалено {deleted_count} дублирующих задач!"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("✨ Дублирующие задачи не найдены")
                )

        # Показываем финальное состояние
        self.stdout.write("\n📊 Текущие активные задачи после очистки:")
        self._show_current_tasks()

    def _list_all_tasks(self):
        """Показывает все существующие периодические задачи"""
        self.stdout.write("\n📋 Все периодические задачи:")

        tasks = PeriodicTask.objects.all().order_by("name")
        if not tasks.exists():
            self.stdout.write("   Задачи не найдены")
            return

        for task in tasks:
            status = "🟢" if task.enabled else "🔴"
            self.stdout.write(f"\n{status} {task.name}")
            self.stdout.write(f"   • ID: {task.id}")
            self.stdout.write(f"   • Задача: {task.task}")
            self.stdout.write(f"   • Расписание: {task.crontab or task.interval}")
            self.stdout.write(f"   • Включена: {task.enabled}")
            if task.description:
                self.stdout.write(f"   • Описание: {task.description}")

        self.stdout.write(f"\n📊 Всего задач: {tasks.count()}")
        enabled_count = tasks.filter(enabled=True).count()
        self.stdout.write(f"🟢 Активных: {enabled_count}")
        self.stdout.write(f"🔴 Отключенных: {tasks.count() - enabled_count}")

    def _show_current_tasks(self):
        """Показывает текущие активные задачи"""
        tasks = PeriodicTask.objects.filter(enabled=True).order_by("name")

        if not tasks.exists():
            self.stdout.write("   Активные задачи не найдены")
            return

        for task in tasks:
            schedule_str = str(task.crontab or task.interval)
            self.stdout.write(f"🟢 {task.name} -> {task.task} ({schedule_str})")

        self.stdout.write(f"📊 Всего активных задач: {tasks.count()}")
