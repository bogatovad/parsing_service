from abc import ABC, abstractmethod
from typing import List, Dict, Any


class NLPProcessorBase(ABC):
    def __init__(self, *args, **kwargs) -> None:
        """
        Конструктор для инициализации NLPProcessorBase.
        Параметры могут быть переданы в зависимости от реализации.
        """
        pass

    @abstractmethod
    def process(self, text: str) -> List[Dict[str, Any]]:
        """
        Обрабатывает текст и возвращает список событий.

        Args:
            text: Текст для обработки

        Returns:
            List[Dict[str, Any]]: Список событий
        """
        pass

    @abstractmethod
    def generate_link_title(self, event_text: str) -> str:
        """
        Генерирует название для ссылки.

        Args:
            event_text: Текст события

        Returns:
            str: Название ссылки
        """
        pass

    @abstractmethod
    def determine_category(
        self, event_text: str, service: str = "category_prompt"
    ) -> str:
        """
        Определяет категорию мероприятия.

        Args:
            event_text: Текст события
            service: Сервис для определения категории

        Returns:
            str: Категория мероприятия
        """
        pass

    @abstractmethod
    def process_post(self, post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Обрабатывает отдельный пост.

        Args:
            post: Данные поста

        Returns:
            List[Dict[str, Any]]: Список событий
        """
        pass
