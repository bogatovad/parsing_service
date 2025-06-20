import re
import hashlib
from typing import List, Dict, Any, Tuple
import logging

from interface_adapters.services.duplicate_filter_interface import (
    DuplicateFilterInterface,
)

logger = logging.getLogger(__name__)


class KudaGoDuplicateFilter(DuplicateFilterInterface):
    """
    Фильтр дубликатов для данных KudaGo.
    """

    def generate_unique_id(self, item: Dict[str, Any]) -> str:
        """
        Генерирует уникальный идентификатор для события KudaGo.
        """
        name = item.get("name", "Default Name FROM KUDA GO")
        location = item.get("location", "Unknown")
        description = item.get("description", "")
        time = item.get("time", "")

        # Создаем строку для хэширования из ключевых полей
        hash_string = f"{name}_{location}_{description[:100]}_{time}"
        # Создаем хэш
        hash_value = hashlib.md5(hash_string.encode("utf-8")).hexdigest()[:8]

        # Создаем уникальный идентификатор с хэшем
        unique_id = f"kudago_{name[:30]}_{hash_value}"

        return self.clean_unique_id(unique_id)

    def filter_duplicates(
        self, items: List[Dict[str, Any]], existing_ids: List[str]
    ) -> List[Tuple[Dict[str, Any], str]]:
        """
        Фильтрует дубликаты в данных KudaGo.
        """
        filtered_items = []
        existing_ids_set = set(existing_ids)  # Используем set для быстрого поиска

        for item in items:
            unique_id = self.generate_unique_id(item)

            if unique_id not in existing_ids_set:
                filtered_items.append((item, unique_id))
                existing_ids_set.add(
                    unique_id
                )  # Добавляем, чтобы избежать дубликатов в рамках одного запуска
            else:
                logger.debug(f"Пропускаем дубликат KudaGo с unique_id: {unique_id}")

        logger.info(
            f"После фильтрации дубликатов осталось {len(filtered_items)} событий KudaGo"
        )
        return filtered_items

    def clean_unique_id(self, unique_id: str) -> str:
        """
        Очищает уникальный идентификатор от проблемных символов.
        """
        return re.sub(r"[^\w\-_]", "_", unique_id)
