from datetime import datetime
import logging
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from usecases.telegram.messages import Message
from usecases.telegram.kandinsky_api import generate_image_with_kandinsky

logging.basicConfig(level=logging.INFO)


class GetContentTgUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo,
        file_repo,
    ) -> None:
        logging.info(Message.INIT)
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self) -> bool:
        sources = self.gateway.get_sources()

        for source, city in sources:
            logging.info(Message.START_GATEWAY_PROCESS)
            logging.info(f"processing {source} {city}")
            raw_contents = self.gateway.fetch_content(source, city)
            logging.info(Message.END_GATEWAY_PROCESS)
            logging.info(f"Всего данных собрано {len(raw_contents)}")

            if not raw_contents:
                return False

            exists_unique_ids = self.content_repo.get_all_unique_ids()

            for raw in raw_contents:
                processed_result = self.nlp_processor.process_post(raw)
                if not processed_result:
                    continue

                image_data = raw.get("image") or b""  # noqa: F841

                for event in processed_result:
                    unique_id = event.get("name", "") + raw.get("channel", "")
                    if unique_id in exists_unique_ids:
                        continue

                    if "image" not in event or not event["image"]:
                        # Если изображение отсутствует – генерируем его через Kandinsky
                        event["image"] = generate_image_with_kandinsky(
                            f"{event.get('name', '')} {event.get('description', '')}"
                        )

                    content = self._create_schema_from_event(event, unique_id)
                    if content:
                        logging.info(Message.CREATE_SCHEMA)
                        logging.info(f"Save content from tg {content}")
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

            date_start = event.get("data_start", datetime.now())
            date_end = event.get("data_end", "")

            current_time = datetime.now()

            if date_end:
                if not (date_start <= current_time <= date_end):
                    logging.info(
                        "Мероприятие не актуально: текущая дата вне интервала [date_start, date_end]."
                    )
                    return None
            else:
                # Если задана только дата начала, проверяем, что она уже наступила
                if not (date_start <= current_time):
                    logging.info(
                        "Мероприятие не актуально: текущая дата позже даты начала."
                    )
                    return None

            return ContentPydanticSchema(
                name=event.get("name", "Default Name FROM TG"),
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
