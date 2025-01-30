from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import ContentRepositoryProtocol
from frameworks_and_drivers.gateways.parsing_gateway.kuda_go_gateway import KudaGoGateway

class GetContentKudaGoUseCase(AbstractUseCase):
    def __init__(self, gateway: BaseGateway,
                 content_repo: ContentRepositoryProtocol, file_repo: FileRepositoryProtocol) -> None:
        self.gateway = gateway
        self.content_repo = content_repo
        self.file_repo = file_repo

    def execute(self) -> list[ContentPydanticSchema]:
        raw_content = self.gateway.fetch_content()

        """
        content = ContentPydanticSchema(
            name=processed_content.get('name', 'Default Name FROM KUDA GO'),
            description=processed_content.get('description', 'No description available'),
            tags=processed_content.get('tags', []),
            image=processed_content.get('image', b'gg'),
            contact=processed_content.get('contact', {}),
            date_start=processed_content.get('date_start', datetime.now()),
            date_end=processed_content.get('date_end', datetime.now()),
            time=processed_content.get('time', '00:00'),
            location=processed_content.get('location', 'Unknown'),
            cost=processed_content.get('cost', 0)
        )
        """
        return raw_content

gateway = KudaGoGateway(client={})
kudago_content_usecase = GetContentKudaGoUseCase(gateway=gateway, content_repo = '', file_repo='')
data = kudago_content_usecase.execute()
#на 03.02.2025 52 события
print(len(data))