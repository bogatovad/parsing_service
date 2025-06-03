import logging
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)


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

        for raw in raw_contents:
            processed_result = self.nlp_processor.process_post(raw)
            if not processed_result:
                continue
            for event in processed_result:
                unique_id = event.get("id", "")
                if unique_id in exists_unique_ids:
                    continue

                # Генерация более уникального идентификатора
                name = event.get("name", "")
                date_str = event.get("data_start", "")
                if date_str and name:
                    unique_id = f"{unique_id}_{date_str}_{name[:50]}"  # Используем первые 50 символов имени
                elif name:
                    unique_id = f"{unique_id}_{name[:50]}"  # Используем первые 50 символов имени

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
