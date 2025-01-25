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
        # todo: этим запросом мы тянем данные из тг. Это сырые данные.
        raw_content: list[dict] = self.gateway.fetch_content()

        # todo: Сырые данные поступают на вход nlp_processor.process которые отдает обработанные данные.
        processed_content = self.nlp_processor.process(raw_content)

        # todo: тут должен быть код, который получает контент из телеграма.
        # todo: и отдает его в list[ContentPydanticSchema].
        # todo: предварительно данные, полученные из тг должны быть обработаны с помошью nlp_processor.
        contents = []

        for content in raw_content:
            tags = [item.get("name", "null") for item in content.get('categories', [])]
            prices = [item.get("price") for item in content.get('cost', [{"price": 0}])]
            contacts = {"link": content.get('url', {})}
            contents.append(
                ContentPydanticSchema(
                    name=content.get('name', 'Default Name FROM TIMEPAD'),
                    description=content.get('description_short', 'No description available'),
                    tags=tags,
                    image=content.get('image', b'data'),
                    contact=contacts,
                    date_start=content.get('starts_at', datetime.now()),
                    date_end=content.get('ends_at', datetime.now()),
                    time=content.get('time', '00:00'),
                    location=content.get('location', 'Unknown').get("address"),
                    cost=min(prices)
                )
            )
        print(f"{contents=}")
        return contents
