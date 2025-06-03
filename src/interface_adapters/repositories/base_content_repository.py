from abc import ABC, abstractmethod
from typing import Optional
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
    def save_one_content(self, content: ContentPydanticSchema) -> None:
        """
        Метод для сохранения одного элемента контента.

        :param content: Элемент контента.
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

    @abstractmethod
    def get_all_unique_ids(self) -> list[str]:
        """
        Метод для получения всех уникальных идентификаторов контента.

        :return: Список уникальных идентификаторов контента.
        """
        raise NotImplementedError

    @abstractmethod
    def find_duplicate(
        self,
        name: str,
        date_start: str,
        time: str,
        location: str,
        similarity_threshold: float = 0.8,
    ) -> Optional[ContentPydanticSchema]:
        """
        Проверяет наличие дубликата события в базе данных.

        :param name: Название события
        :param date_start: Дата начала события
        :param time: Время события
        :param location: Место проведения
        :param similarity_threshold: Порог схожести для нечеткого сравнения (0.0 - 1.0)
        :return: Найденный дубликат или None
        """
        raise NotImplementedError
