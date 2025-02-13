from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)


class GetContentKudaGoUseCase(AbstractUseCase):
    def __init__(
        self,
        gateway: BaseGateway,
        content_repo: ContentRepositoryProtocol,
        nlp_processor: NLPProcessorBase,
        file_repo: FileRepositoryProtocol,
    ) -> None:
        self.gateway = gateway
        self.content_repo = content_repo
        self.file_repo = file_repo
        self.nlp_processor = nlp_processor

    def execute(self) -> list[ContentPydanticSchema]:
        raw_content = self.gateway.fetch_content()
        result = []

        # TODO: тут хранится список тегов которые есть в приложении.
        # TODO: наша задача определить какой из этих тегов НАИБОЛЕЕ близок к element.get('tags', []) и выбрать его
        names = self.content_repo.get_all_name_contents()
        for element in raw_content:
            if element.get("name") not in names:
                content_element = ContentPydanticSchema(
                    name=element.get("name", "Default Name FROM KUDA GO"),
                    description=element.get("description", "No description available"),
                    tags=element.get("tags", []),
                    image=element.get("image", b"data"),
                    # TODO: тут задача в том чтобы сгенерировать имя ссылки (вместо текущего "Ссылка"), это делается через nlp_processor.
                    contact={"Ссылка: ": element.get("url", {})},
                    date_start=element.get("date_start", datetime.now()),
                    date_end=element.get("date_end", datetime.now()),
                    time=element.get("time", "00:00"),
                    location=element.get("location", "Unknown"),
                    cost=element.get("cost", 0),
                    city=element.get("city", ""),
                )
                result.append(content_element)
        if result:
            self.content_repo.save_content(result)
        return result
