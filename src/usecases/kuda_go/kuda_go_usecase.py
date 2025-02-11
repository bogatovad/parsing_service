from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import ContentRepositoryProtocol
from frameworks_and_drivers.gateways.parsing_gateway.kuda_go_gateway import KudaGoGateway
from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_gateway import NLPProcessor

class GetContentKudaGoUseCase(AbstractUseCase):
    def __init__(self, gateway: BaseGateway, nlp_processor : NLPProcessorBase,
                 content_repo: ContentRepositoryProtocol, file_repo: FileRepositoryProtocol) -> None:
        self.gateway = gateway
        self.content_repo = content_repo
        self.file_repo = file_repo
        self.nlp_processor = nlp_processor

    def execute(self) -> list[ContentPydanticSchema]:
        raw_content = self.gateway.fetch_content()
        result = []

        for element in raw_content:

            processed_link_name = self.nlp_processor.generate_link_name_by_description(element.get('description'))
            processed_categories = self.nlp_processor.determine_category(element.get('description'))

            content_element = ContentPydanticSchema(
                name=element.get('name', 'Default Name FROM KUDA GO'),
                description=element.get('description', 'No description available'),
                tags=[processed_categories],
                image=element.get('image', b'gg'),
                contact=[{processed_link_name : element.get('url', {})}],
                date_start=element.get('date_start', datetime.now()),
                date_end=element.get('date_end', datetime.now()),
                time=element.get('time', '00:00'),
                location=element.get('location', 'Unknown'),
                cost=element.get('cost', 0),
                city = element.get('city', '')
            )
            result.append(content_element)
        return result

gateway = KudaGoGateway(client={})
nlp_processor = NLPProcessor()
kudago_content_usecase = GetContentKudaGoUseCase(gateway=gateway, content_repo = '', file_repo='', nlp_processor=nlp_processor)
data = kudago_content_usecase.execute()
#на 03.02.2025 52 события
print(data[0].dict(exclude={'image'}))