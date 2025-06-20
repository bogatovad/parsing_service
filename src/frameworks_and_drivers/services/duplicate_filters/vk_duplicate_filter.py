import re
from typing import List, Dict, Any, Tuple
import logging

from interface_adapters.services.duplicate_filter_interface import (
    DuplicateFilterInterface,
)

logger = logging.getLogger(__name__)


class VkDuplicateFilter(DuplicateFilterInterface):
    """
    Фильтр дубликатов для данных VK.
    """

    def generate_unique_id(self, item: Dict[str, Any]) -> str:
        """
        Генерирует уникальный идентификатор для поста VK.
        """
        original_id = item.get("id", "")
        text = item.get("text", "")

        # Создаем базовый unique_id
        if original_id:
            unique_id = f"vk_{original_id}"
        else:
            # Если нет ID, создаем на основе первых слов текста
            text_part = text[:50] if text else "no_text"
            unique_id = f"vk_{text_part}"

        return self.clean_unique_id(unique_id)

    def filter_duplicates(
        self, items: List[Dict[str, Any]], existing_ids: List[str]
    ) -> List[Tuple[Dict[str, Any], str]]:
        """
        Фильтрует дубликаты в данных VK.
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
                logger.debug(f"Пропускаем дубликат VK с unique_id: {unique_id}")

        logger.info(
            f"После фильтрации дубликатов осталось {len(filtered_items)} постов VK"
        )
        return filtered_items

    def clean_unique_id(self, unique_id: str) -> str:
        """
        Очищает уникальный идентификатор от проблемных символов.
        """
        return re.sub(r"[^\w\-_]", "_", unique_id)
