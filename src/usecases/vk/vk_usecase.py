import logging
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],  # Чтобы лог был и в консоли (Docker log)
)

logger = logging.getLogger(__name__)


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
        sources = self.gateway.get_sources()  # correct
        for source in sources:
            raw_content = self.gateway.fetch_content(source)
            if not raw_content:
                continue

            exists_unique_ids = self.content_repo.get_all_unique_ids()

            for raw in raw_content:
                processed_result = self.nlp_processor.process_post(raw)
                if not processed_result:
                    logger.info("Контента нет:")
                    continue

                for event in processed_result:
                    unique_id = event.get("id", "")
                    if unique_id in exists_unique_ids:
                        logger.info(f"Пост уже добавлен.")
                        continue

                    content = self._create_schema_from_event(event, unique_id)
                    if content:
                        logger.info("Схема создана")
                        logger.info(f"Save content from VK")
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

            date_start = event.get("data_start", "")
            date_end = event.get("data_end", "")
            if not date_start:
                logging.info("Нет даты начала.")
                return None
            current_date = datetime.now()
            date_end = datetime.strptime(date_end, "%Y-%m-%d")
            if current_date > date_end:
                logging.info("Мероприятие завершено.")
                return None

            return ContentPydanticSchema(
                name=event.get("name", "Default Name FROM VK"),
                description=event.get("description", "No description available"),
                tags=event.get("category", []),
                image=event.get("image", b""),
                contact=event.get("contact", [{}]),
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
