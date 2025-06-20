from datetime import datetime, timedelta
from typing import Dict, Any
import logging

from interface_adapters.services.event_validator_interface import (
    EventValidatorInterface,
)

logger = logging.getLogger(__name__)


class DateEventValidator(EventValidatorInterface):
    """
    Валидатор событий на основе дат.
    Проверяет, что события не устарели и имеют корректные даты.
    """

    def __init__(self, max_past_days: int = 1):
        """
        Инициализирует валидатор.

        Args:
            max_past_days: Максимальное количество дней в прошлом для валидных событий
        """
        self.max_past_days = max_past_days

    def is_event_valid(self, event: Dict[str, Any]) -> bool:
        """
        Проверяет, является ли событие валидным.
        """
        date_start = event.get("date_start")
        date_end = event.get("date_end")

        if not date_start:
            logger.debug("Событие без даты начала считается невалидным")
            return False

        # Если date_start это строка, пытаемся конвертировать в datetime
        if isinstance(date_start, str):
            try:
                date_start = datetime.fromisoformat(date_start)
            except ValueError:
                logger.debug(f"Не удалось преобразовать дату: {date_start}")
                return False

        # Если date_end это строка, пытаемся конвертировать в datetime
        if isinstance(date_end, str):
            try:
                date_end = datetime.fromisoformat(date_end)
            except ValueError:
                date_end = date_start  # Если не получилось, используем дату начала

        return self.is_date_valid(date_start, date_end)

    def is_date_valid(self, date_start: datetime, date_end: datetime = None) -> bool:
        """
        Проверяет валидность дат события.
        """
        if not isinstance(date_start, datetime):
            return False

        current_date = datetime.now()
        min_valid_date = current_date - timedelta(days=self.max_past_days)

        # Проверяем, что событие не слишком старое
        if date_start < min_valid_date:
            return False

        # Если есть дата окончания, проверяем её
        if date_end and isinstance(date_end, datetime):
            if date_end < min_valid_date:
                return False
            # Проверяем, что дата окончания не раньше даты начала
            if date_end < date_start:
                return False

        return True

    def get_validation_errors(self, event: Dict[str, Any]) -> list:
        """
        Возвращает список ошибок валидации для события.
        """
        errors = []

        date_start = event.get("date_start")
        date_end = event.get("date_end")

        if not date_start:
            errors.append("Отсутствует дата начала события")
            return errors

        # Конвертируем строки в datetime если необходимо
        if isinstance(date_start, str):
            try:
                date_start = datetime.fromisoformat(date_start)
            except ValueError:
                errors.append(f"Некорректный формат даты начала: {date_start}")
                return errors

        if isinstance(date_end, str):
            try:
                date_end = datetime.fromisoformat(date_end)
            except ValueError:
                errors.append(f"Некорректный формат даты окончания: {date_end}")

        current_date = datetime.now()
        min_valid_date = current_date - timedelta(days=self.max_past_days)

        if date_start < min_valid_date:
            errors.append(f"Событие слишком старое: {date_start}")

        if date_end and isinstance(date_end, datetime):
            if date_end < min_valid_date:
                errors.append(f"Дата окончания слишком старая: {date_end}")
            if date_end < date_start:
                errors.append("Дата окончания раньше даты начала")

        return errors
