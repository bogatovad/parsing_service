from abc import ABC, abstractmethod
from interface_adapters.presenters.schemas import ContentPydanticSchema


class ContentRepositoryProtocol(ABC):
    @abstractmethod
    def save_content(self, contents: list[ContentPydanticSchema]) -> None:
        """
        Метод для сохранения контента.

        :param contents: Список контента.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_tags(self) -> list[str]:
        """
        Метод для получения всех тегов.

        :return: Список тегов.
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_name_contents(self) -> list[str]:
        """
        Метод для получения всех имен контентов.

        :return: Список имен событий.
        """
        raise NotImplementedError

    def get_all_unique_ids(self) -> list[str]:
        """
        Метод для получения всех уникальных идентификаторов контента.

        :return: Список уникальных идентификаторов контента.
        """
        raise NotImplementedError
