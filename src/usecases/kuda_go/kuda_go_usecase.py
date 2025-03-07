from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.presenters.schemas import ContentPydanticSchema
from usecases.common import AbstractUseCase
from datetime import datetime
from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
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

        exists_unique_ids = self.content_repo.get_all_unique_ids()  # noqa: F841

        for element in raw_content:


            unique_id = element.get("name", "Default Name FROM KUDA GO")

            if unique_id in exists_unique_ids:
                continue
            
            processed_link_name = self.nlp_processor.generate_link_title(
                element.get("description")
            )
            processed_categories = self.nlp_processor.determine_category(
                element.get("description")
            )


            content_element = ContentPydanticSchema(
                name=element.get("name", "Default Name FROM KUDA GO"),
                description=element.get("description", "No description available"),
                tags=[processed_categories],
                image=element.get("image", b"gg"),
                сontact=[{processed_link_name: element.get("url", {})}],
                date_start=element.get("date_start", datetime.now()),
                date_end=element.get("date_end", datetime.now()),
                time=element.get("time", "00:00"),
                location=element.get("location", "Unknown"),
                cost=element.get("cost", 0),
                city=element.get("city", ""),
                unique_id=element.get("name", "Default Name FROM KUDA GO"),
            )

            result.append(content_element)
        self.content_repo.save_content(result)
        return result

'''
if __name__ == '__main__':
    this_class = GetContentKudaGoUseCase(gateway=KudaGoGateway(), content_repo=None, nlp_processor=None, file_repo=None)
    rst = this_class.execute()
    print(rst)
    with open('kgd.json', 'w', encoding='utf-8') as kgd:
        new = json.dumps(rst, ensure_ascii=False, indent=4)
        kgd.write(new)
    print('ready')
'''