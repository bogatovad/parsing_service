from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from usecases.telegram.messages import Message
from datetime import datetime
import logging


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

    def execute(self) -> list[ContentPydanticSchema]:
        """
        Алгоритм:
         1. Получаем сырые данные из Telegram через gateway.
         2. Для каждого сообщения обрабатываем текст через nlp_processor.
         3. Обрабатываем каждое событие от нейронки.
         4. Приводим поля к ожидаемым типам (например, contact – к списку, cost – к целому).
         5. Формируем объект ContentPydanticSchema для каждого события.
         6. Возвращаем список объектов.
        """
        logging.info(Message.START_GATEWAY_PROCESS)
        raw_contents = self.gateway.fetch_content()
        logging.info(Message.END_GATEWAY_PROCESS)
        logging.info(f"Всего данных собрано {len(raw_contents)}")
        if not raw_contents:
            return []

        exists_unique_ids = self.content_repo.get_all_unique_ids()
        results = []

        for index, raw in enumerate(raw_contents):
            unique_id = raw.get("event_id") + raw.get("channel")

            if unique_id in exists_unique_ids:
                continue

            processed_result = self.nlp_processor.process_post(raw)

            if not processed_result:
                continue

            image_data = raw.get("image") or b""

            for event in processed_result:
                if "image" not in event or event.get("image") is None:
                    event["image"] = image_data

                content = self._create_schema_from_event(event)

                if content:
                    logging.info(Message.CREATE_SCHEMA)
                    results.append(content)

        logging.info(f"Всего объектов создано {len(results)}")
        self.content_repo.save_content(results)
        return results

    @staticmethod
    def _create_schema_from_event(event: dict) -> ContentPydanticSchema | None:
        try:
            cost_raw = event.get("cost", 0)
            try:
                cost = int(cost_raw)
            except (ValueError, TypeError):
                cost = 0
            unique_id = event.get("event_id") + event.get("channel")
            return ContentPydanticSchema(
                name=event.get("name", "Default Name FROM TG"),
                description=event.get("description", "No description available"),
                tags=event.get("category", []),
                image=event.get("image") or b"",
                contact=event.get("contact", [{}]),
                date_start=event.get("data_start", datetime.now()),
                date_end=event.get("data_end", datetime.now()),
                time=event.get("time", "00:00"),
                location=event.get("location", "Unknown"),
                cost=cost,
                city=event.get("city", "Unknown"),
                unique_id=unique_id,
            )
        except Exception:
            logging.info(Message.ERROR_CREATE_SCHEMA)
            return None
