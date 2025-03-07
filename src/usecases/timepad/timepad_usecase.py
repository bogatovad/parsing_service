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
        unique_names = []

        for content in raw_content:
            try:
                if not content:
                    continue

                if content.get("name") in unique_names:
                    continue
                else:
                    unique_names.append(content.get("name"))

                logging.info(f"Processing content from Timepad {content}")
                unique_id = str(content.get("id")) + "timepad"

                if unique_id in unique_ids:
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
                clean_name = html.unescape(name).replace("�", "")
                description = content.get("description_short")
                clean_description = html.unescape(description).replace("�", "")
                location = content.get("location").get("address")
                clean_location = html.unescape(location).replace("�", "")
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
