import os
import io
import uuid
import logging
from django.core.files import File

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)
from frameworks_and_drivers.django.parsing.data_manager.models import Content, Tags
from interface_adapters.presenters.schemas import ContentPydanticSchema
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)

logging.basicConfig(level=logging.INFO)


class DjangoContentRepository(ContentRepositoryProtocol):
    def save_content(self, contents: list[ContentPydanticSchema]) -> None:
        """
        Метод для сохранения контента.

        :param contents: Список контента для сохранения
        """
        for content in contents:
            try:
                content_for_save = Content(
                    name=content.name,
                    description=content.description,
                    contact=content.contact,
                    date_start=content.date_start,
                    date_end=content.date_end,
                    time=content.time,
                    location=content.location,
                    cost=content.cost,
                    city=content.city,
                    unique_id=content.unique_id,
                    event_type=content.event_type,
                    publisher_type=content.publisher_type,
                    publisher_id=content.publisher_id,
                )
                if content.image:
                    buffer = io.BytesIO(content.image)
                    content_for_save.image.save(
                        name=f"autopost{uuid.uuid4()}", content=File(buffer)
                    )
                content_for_save.save()
                for tag in content.tags:
                    tag_for_save = Tags.objects.filter(name=tag).first()
                    if tag_for_save:
                        content_for_save.tags.add(tag_for_save)
            except Exception as e:
                logging.error(f"Ошибка при сохранении контента: {str(e)}")

    def save_one_content(self, content: ContentPydanticSchema) -> None:
        try:
            name = content.name.strip() if content.name else "Без названия"
            description = (
                content.description.strip()
                if content.description
                else "Описание отсутствует"
            )
            location = (
                content.location.strip()
                if content.location
                else "Место проведения уточняется"
            )
            time = content.time.strip() if content.time else None
            city = content.city.strip() if content.city else "nn"

            # Создаем объект контента
            content_for_save = Content(
                name=name,
                description=description,
                contact=content.contact or [],
                date_start=content.date_start,
                date_end=content.date_end,
                time=time,
                location=location,
                cost=content.cost or 0,
                city=city,
                unique_id=content.unique_id,
                event_type=content.event_type or "offline",
                publisher_type=content.publisher_type or "user",
                publisher_id=content.publisher_id or 1_000_000,
            )

            # Сохраняем изображение, если оно есть
            if content.image:
                try:
                    if len(content.image) > 0:
                        buffer = io.BytesIO(content.image)

                        try:
                            from PIL import Image

                            Image.open(buffer).verify()
                            buffer.seek(0)
                            image_filename = f"autopost_{content.unique_id or 'no_id'}_{uuid.uuid4()}.jpg"
                            logging.info(
                                f"Attempting to save image {image_filename} to MinIO for content: {content.name}"
                            )
                            content_for_save.image.save(
                                name=image_filename, content=File(buffer)
                            )
                            logging.info(
                                f"Successfully saved image {image_filename} to MinIO."
                            )
                        except Exception as img_verify_error:
                            logging.error(
                                f"Invalid image data: {str(img_verify_error)}"
                            )
                    else:
                        logging.warning("Empty image data received")
                except Exception as img_error:
                    logging.error(
                        f"Error saving image for {content.name}: {str(img_error)}"
                    )

            # Сохраняем основной объект
            content_for_save.save()

            # Обрабатываем теги
            for tag_name in content.tags:
                if not tag_name:
                    continue
                try:
                    tag_name = tag_name.strip()
                    tag_for_save = Tags.objects.filter(name__iexact=tag_name).first()

                    if not tag_for_save:
                        tag_for_save = Tags.objects.create(
                            name=tag_name, description=f"Tag for {name}"
                        )

                    content_for_save.tags.add(tag_for_save)
                except Exception as tag_error:
                    logging.warning(
                        f"Ошибка при сохранении тега {tag_name}: {str(tag_error)}"
                    )

            logging.info(f"Успешно сохранено событие: {name}")

        except Exception as ex:
            logging.error(f"Ошибка при сохранении контента: {str(ex)}")
            raise

    def get_all_tags(self) -> list[str]:
        return list(Tags.objects.values_list("name", flat=True))

    def get_all_name_contents(self) -> list[str]:
        return list(Content.objects.values_list("name", flat=True))

    def get_all_unique_ids(self) -> list[str]:
        return list(Content.objects.values_list("unique_id", flat=True))

    def all_today_contents(self) -> Content:
        """
        Метод для получения всех событий на сегодня.
        """
        pass
