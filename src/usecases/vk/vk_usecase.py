import logging
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
import re


logger = logging.getLogger("logger_vk_usecase")
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)


logger.addHandler(console_handler)


class GetContentVkUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo,
        file_repo,
    ) -> None:
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self) -> bool:
        raw_contents = self.gateway.fetch_content()
        logger.info(f"Всего данных собрано {len(raw_contents)}")

        if not raw_contents:
            return False

        exists_unique_ids = self.content_repo.get_all_unique_ids()

        # Фильтруем сырые данные - убираем дубликаты ДО дорогой NLP обработки
        filtered_raw_contents = []
        for raw in raw_contents:
            # Генерируем unique_id на основе сырых данных
            original_id = raw.get("id", "")
            text = raw.get("text", "")

            # Создаем базовый unique_id
            if original_id:
                unique_id = f"vk_{original_id}"
            else:
                # Если нет ID, создаем на основе первых слов текста
                text_part = text[:50] if text else "no_text"
                unique_id = f"vk_{text_part}"

            # Очищаем от проблемных символов
            unique_id = re.sub(r"[^\w\-_]", "_", unique_id)

            if unique_id not in exists_unique_ids:
                filtered_raw_contents.append(raw)
                exists_unique_ids.append(
                    unique_id
                )  # Добавляем, чтобы избежать дубликатов в рамках одного запуска
            else:
                logger.debug(f"Пропускаем дубликат VK с unique_id: {unique_id}")

        logger.info(
            f"После фильтрации дубликатов осталось {len(filtered_raw_contents)} постов для NLP обработки"
        )

        # Теперь обрабатываем только уникальные посты
        for raw in filtered_raw_contents:
            processed_result = self.nlp_processor.process_post(raw)
            if not processed_result:
                continue
            for event in processed_result:
                # Генерируем тот же unique_id, что и при фильтрации
                original_id = raw.get("id", "")
                if original_id:
                    unique_id = f"vk_{original_id}"
                else:
                    text = raw.get("text", "")
                    text_part = text[:50] if text else "no_text"
                    unique_id = f"vk_{text_part}"

                unique_id = re.sub(r"[^\w\-_]", "_", unique_id)

                content = self._create_schema_from_event(event, unique_id)
                if content:
                    logger.info("Схема создана")
                    logger.info("Save content from VK")
                    self.content_repo.save_one_content(content)
        return True

    @staticmethod
    def _create_schema_from_event(
        event: dict, unique_id: str
    ) -> ContentPydanticSchema | None:
        try:
            cost_raw = event.get("cost", 0)
            try:
                cost = int(cost_raw)
            except (ValueError, TypeError):
                cost = 0

            # Обработка дат
            date_start_str = event.get("data_start", "")
            date_end_str = event.get("data_end", date_start_str)

            if not date_start_str:
                logging.info("Нет даты начала.")
                return None

            try:
                date_start = datetime.strptime(date_start_str, "%Y-%m-%d")
                date_end = datetime.strptime(date_end_str, "%Y-%m-%d")
                current_date = datetime.now()

                if current_date > date_end:
                    logging.info("Мероприятие завершено.")
                    return None
            except ValueError as e:
                logging.error(f"Ошибка парсинга даты: {e}")
                return None

            # Обработка контактов
            contact = event.get("contact", [{}])
            if isinstance(contact, dict):
                contact = [contact]
            elif not isinstance(contact, list):
                contact = [{}]

            return ContentPydanticSchema(
                name=event.get("name", "Default Name FROM VK"),
                description=event.get("description", "No description available"),
                tags=event.get("category", []),
                image=event.get("image", b""),
                contact=contact,
                date_start=date_start,
                date_end=date_end,
                time=event.get("time", "00:00"),
                location=event.get("location", "Unknown"),
                cost=cost,
                city=event.get("city", "Unknown"),
                unique_id=unique_id,
            )
        except Exception as e:
            logging.error(f"Ошибка при создании схемы: {e}", exc_info=True)
            return None
