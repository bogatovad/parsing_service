from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple


class DuplicateFilterInterface(ABC):
    """
    Интерфейс для фильтрации дубликатов в данных.
    Позволяет абстрагировать логику определения и фильтрации дубликатов.
    """

    @abstractmethod
    def generate_unique_id(self, item: Dict[str, Any]) -> str:
        """
        Генерирует уникальный идентификатор для элемента.

        Args:
            item: Элемент данных

        Returns:
            str: Уникальный идентификатор
        """
        pass

    @abstractmethod
    def filter_duplicates(
        self, items: List[Dict[str, Any]], existing_ids: List[str]
    ) -> List[Tuple[Dict[str, Any], str]]:
        """
        Фильтрует дубликаты из списка элементов.

        Args:
            items: Список элементов для фильтрации
            existing_ids: Список уже существующих идентификаторов

        Returns:
            List[Tuple[Dict[str, Any], str]]: Список кортежей (элемент, unique_id)
        """
        pass

    @abstractmethod
    def clean_unique_id(self, unique_id: str) -> str:
        """
        Очищает уникальный идентификатор от недопустимых символов.

        Args:
            unique_id: Исходный идентификатор

        Returns:
            str: Очищенный идентификатор
        """
        pass
