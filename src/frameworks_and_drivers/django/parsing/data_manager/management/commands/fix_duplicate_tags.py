from django.core.management.base import BaseCommand
from django.db.models import Count
from frameworks_and_drivers.django.parsing.data_manager.models import Tags, Content
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Находит и объединяет дублирующиеся теги"

    def handle(self, *args, **options):
        # Находим дублирующиеся теги
        duplicates = (
            Tags.objects.values("name")
            .annotate(name_count=Count("id"))
            .filter(name_count__gt=1)
        )

        self.stdout.write(f"Найдено {len(duplicates)} дублирующихся тегов")

        # Обрабатываем каждый дублирующийся тег
        for duplicate in duplicates:
            tag_name = duplicate["name"]
            self.stdout.write(f"\nОбработка дубликатов тега: {tag_name}")

            # Получаем все экземпляры тега с этим именем
            tags = Tags.objects.filter(name=tag_name).order_by("id")

            if not tags:
                continue

            # Используем первый тег как основной
            primary_tag = tags.first()
            duplicate_tags = tags.exclude(id=primary_tag.id)

            self.stdout.write(f"Основной тег ID: {primary_tag.id}")

            # Для каждого дубликата
            for tag in duplicate_tags:
                try:
                    # Получаем все связанные контенты
                    contents = Content.objects.filter(tags=tag)

                    # Добавляем их к основному тегу
                    for content in contents:
                        content.tags.remove(tag)
                        content.tags.add(primary_tag)

                    self.stdout.write(
                        f"Перемещено {contents.count()} контентов с тега ID {tag.id} на тег ID {primary_tag.id}"
                    )

                    # Удаляем дубликат
                    tag.delete()
                    self.stdout.write(f"Удален дублирующийся тег ID: {tag.id}")

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Ошибка при обработке тега {tag.id}: {str(e)}"
                        )
                    )
                    logger.error(
                        f"Error processing tag {tag.id}: {str(e)}", exc_info=True
                    )

        self.stdout.write(self.style.SUCCESS("\nОбработка дубликатов завершена"))
