from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import ContentRepositoryProtocol


class GetContentTimepadUseCase(AbstractUseCase):
    def __init__(self, gateway: BaseGateway, nlp_processor: NLPProcessorBase,
                 content_repo: ContentRepositoryProtocol, file_repo: FileRepositoryProtocol) -> None:
        self.gateway = gateway
        self.nlp_processor = nlp_processor

    def execute(self) -> list[ContentPydanticSchema]:
        # todo: этим запросом мы тянем данные из timepad. Это сырые данные.
        raw_content: list[dict] = self.gateway.fetch_content()

        # todo: Сырые данные поступают на вход nlp_processor.process которые отдает обработанные данные.
        processed_content = self.nlp_processor.process(raw_content)

        # todo: тут должен быть код, который получает контент из timepad.
        # todo: и отдает его в list[ContentPydanticSchema].
        # todo: предварительно данные, полученные из тг должны быть обработаны с помошью nlp_processor.
        contents = []

        for content in raw_content:
            tags = [item.get("name") for item in content.get('categories')]
            prices = [item.get("price") for item in content.get('ticket_types')]
            contacts = {"link": content.get('url', {})}
            datetime_obj = datetime.strptime(content.get('starts_at'), "%Y-%m-%dT%H:%M:%S%z")
            date_end = content.get('ends_at')
            date_end = datetime.strptime(date_end, "%Y-%m-%dT%H:%M:%S%z") if date_end else None
            city = content.get('location').get("city")
            contents.append(
                ContentPydanticSchema(
                    name=content.get('name'),
                    description=content.get('description_short'),
                    tags=tags,
                    image=content.get('image', b'data'),
                    contact=contacts,
                    date_start=datetime.strptime(content.get('starts_at'), "%Y-%m-%dT%H:%M:%S%z"),
                    date_end=date_end,
                    time=datetime_obj.strftime("%H:%M"),
                    location=content.get('location').get("address"),
                    cost=min(prices),
                    city=city
                )
            )
        return contents
