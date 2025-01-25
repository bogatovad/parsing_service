from abc import ABC, abstractmethod

from interface_adapters.dtos.content_dto import ContentDto


class ContentRepositoryProtocol(ABC):
    @abstractmethod
    def save_content(self, content_dto: ContentDto) -> None:
        """
        Метод для сохранения контента.

        :param content_dto: Объект с данными контента, который должен быть сохранен.
        """
        raise NotImplementedError
