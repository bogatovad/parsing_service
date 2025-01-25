from interface_adapters.dtos.content_dto import ContentDto
from interface_adapters.repositories.base_content_repository import ContentRepositoryProtocol


class ContentRepositoryProtocol(ContentRepositoryProtocol):
    def save_content(self, content_dto: ContentDto) -> None:
        """
        Метод для сохранения контента.

        :param content_dto: Объект с данными контента, который должен быть сохранен.
        """
        return []
