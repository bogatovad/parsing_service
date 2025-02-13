import os
import io
import uuid
from django.core.files import File

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)
from frameworks_and_drivers.django.parsing.data_manager.models import Content, Tags
from interface_adapters.presenters.schemas import ContentPydanticSchema
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)


class ContentRepositoryProtocol(ContentRepositoryProtocol):
    def save_content(self, contents: list[ContentPydanticSchema]) -> None:
        """
        Метод для сохранения контента.

        :param contents:
        """
        for content in contents:
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
            )
            print(f"{content=}")
            buffer = io.BytesIO(content.image)
            content_for_save.image.save(
                name=f"autopost{uuid.uuid4()}", content=File(buffer)
            )
            content_for_save.save()
            for tag in content.tags:
                tag_for_save = Tags.objects.filter(name=tag).first()
                if tag_for_save:
                    content_for_save.tags.add(tag_for_save)

    def get_all_tags(self) -> list[str]:
        return list(Tags.objects.values_list("name", flat=True))

    def get_all_name_contents(self) -> list[str]:
        return list(Content.objects.values_list("name", flat=True))
