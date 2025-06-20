from abc import ABC, abstractmethod
from typing import Dict, Any
from datetime import datetime


class EventValidatorInterface(ABC):
    """
    Интерфейс для валидации событий.
    Позволяет абстрагировать логику проверки событий по различным критериям.
    """

    @abstractmethod
    def is_event_valid(self, event: Dict[str, Any]) -> bool:
        """
        Проверяет, является ли событие валидным.

        Args:
            event: Данные события

        Returns:
            bool: True если событие валидно
        """
        pass

    @abstractmethod
    def is_date_valid(self, date_start: datetime, date_end: datetime = None) -> bool:
        """
        Проверяет валидность дат события.

        Args:
            date_start: Дата начала события
            date_end: Дата окончания события (опционально)

        Returns:
            bool: True если даты валидны
        """
        pass

    @abstractmethod
    def get_validation_errors(self, event: Dict[str, Any]) -> list:
        """
        Возвращает список ошибок валидации для события.

        Args:
            event: Данные события

        Returns:
            list: Список ошибок валидации
        """
        pass
