import requests
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)
import logging
import html


logging.basicConfig(level=logging.INFO)


class GetContentTimepadUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo: ContentRepositoryProtocol,
        file_repo: FileRepositoryProtocol,
    ) -> None:
        self.gateway = gateway
        self.nlp_processor = nlp_processor
        self.content_repo = content_repo
        self.cities = {"Нижний Новгород": "nn"}

    def execute(self) -> bool:
        logging.info("Fetching content from Timepad")
        raw_content: list[dict] = self.gateway.fetch_content()
        unique_ids = self.content_repo.get_all_unique_ids()

        # Фильтруем сырые данные - убираем дубликаты ДО дорогой обработки
        filtered_raw_content = []
        for content in raw_content:
            if not content:
                continue

            unique_id = str(content.get("id")) + "_timepad"

            if unique_id not in unique_ids:
                filtered_raw_content.append(content)
                unique_ids.append(
                    unique_id
                )  # Добавляем, чтобы избежать дубликатов в рамках одного запуска
            else:
                logging.debug(f"Пропускаем дубликат Timepad с unique_id: {unique_id}")

        logging.info(
            f"После фильтрации дубликатов осталось {len(filtered_raw_content)} событий для обработки"
        )

        # Теперь обрабатываем только уникальные события
        for content in filtered_raw_content:
            try:
                logging.info(f"Processing content from Timepad {content}")
                unique_id = str(content.get("id")) + "_timepad"

                # Валидация дат - пропускаем устаревшие события
                try:
                    date_start = datetime.strptime(
                        content.get("starts_at"), "%Y-%m-%dT%H:%M:%S%z"
                    )
                    date_end = content.get("ends_at")
                    date_end = (
                        datetime.strptime(date_end, "%Y-%m-%dT%H:%M:%S%z")
                        if date_end
                        else None
                    )

                    if not self._is_event_valid(date_start, date_end):
                        logging.info(
                            f"Пропускаем устаревшее событие Timepad: {content.get('name', 'Unknown')}"
                        )
                        continue
                except Exception as e:
                    logging.error(f"Ошибка при валидации даты Timepad: {e}")
                    continue

                try:
                    logging.info(f"{content=}")
                    if "poster_image" in content:
                        image_url = "https:" + content.get("poster_image").get(
                            "uploadcare_url"
                        )
                    else:
                        if "organization" in content:
                            image_url = (
                                "https:"
                                + content["organization"]["logo_image"][
                                    "uploadcare_url"
                                ]
                            )
                    response = requests.get(image_url)
                    response.raise_for_status()
                    content_bytes = response.content
                except AttributeError:
                    # todo: тут надо генерить картинку через кандинского.
                    # todo: мы попадаем сюда из-за того чтобы картинка не пришла в апи
                    # todo: значит можно и нужно ее генерировать самим.
                    content_bytes = b""

                tags = [item.get("name") for item in content.get("categories")]
                prices = [item.get("price") for item in content.get("ticket_types")]
                processed_link_name = self.nlp_processor.generate_link_title(
                    content.get("description_short")
                )
                processed_categories = self.nlp_processor.determine_category(
                    content.get("description_short") + ",".join(tags)
                )
                contacts = [{processed_link_name: content.get("url", {})}]
                datetime_obj = datetime.strptime(
                    content.get("starts_at"), "%Y-%m-%dT%H:%M:%S%z"
                )
                date_end = content.get("ends_at")
                date_end = (
                    datetime.strptime(date_end, "%Y-%m-%dT%H:%M:%S%z")
                    if date_end
                    else None
                )
                city = content.get("location").get("city")
                name = content.get("name")
                clean_name = html.unescape(name).replace("", "")
                description = content.get("description_short")
                clean_description = html.unescape(description).replace("", "")
                location = content.get("location").get("address")
                clean_location = html.unescape(location).replace("", "")
                clean_location = clean_location if clean_location else ""
                schema = ContentPydanticSchema(
                    name=clean_name,
                    description=clean_description,
                    tags=[processed_categories],
                    image=content_bytes,
                    contact=contacts,
                    date_start=datetime.strptime(
                        content.get("starts_at"), "%Y-%m-%dT%H:%M:%S%z"
                    ),
                    date_end=date_end,
                    time=datetime_obj.strftime("%H:%M"),
                    location=clean_location,
                    cost=min(prices),
                    city=self.cities.get(city),
                    unique_id=unique_id,
                )
                logging.info(f"Saving content to database {schema.name}")
                self.content_repo.save_one_content(schema)
            except:  # noqa: E722
                continue
        return True

    @staticmethod
    def _is_event_valid(date_start, date_end):
        """
        Проверяет, что событие не устарело.
        Возвращает False для событий которые уже завершились.
        """
        try:
            from django.utils import timezone

            # Используем timezone-aware текущую дату
            current_date = timezone.now()

            # Если есть дата окончания, проверяем её
            if date_end and isinstance(date_end, datetime):
                # Если date_end timezone-naive, делаем её aware
                if date_end.tzinfo is None:
                    date_end = timezone.make_aware(date_end)
                return current_date <= date_end

            # Если нет даты окончания, проверяем дату начала
            if isinstance(date_start, datetime):
                # Если date_start timezone-naive, делаем её aware
                if date_start.tzinfo is None:
                    date_start = timezone.make_aware(date_start)
                return current_date <= date_start

            # Если даты не datetime объекты, считаем событие валидным
            return True

        except Exception as e:
            logging.error(f"Ошибка при валидации даты: {e}")
            return True  # В случае ошибки не блокируем событие
