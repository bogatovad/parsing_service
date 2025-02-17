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


class GetContentTgUseCase(AbstractUseCase):
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

    def execute(self) -> list[ContentPydanticSchema]:
        # todo: этим запросом мы тянем данные из тг. Это сырые данные.
        # raw_content = self.gateway.fetch_content()
        #
        # # todo: Сырые данные поступают на вход nlp_processor.process которые отдает обработанные данные.
        # processed_content = self.nlp_processor.process(raw_content)

        # todo: тут должен быть код, который получает контент из телеграма.
        # todo: и отдает его в list[ContentPydanticSchema].
        # todo: предварительно данные, полученные из тг должны быть обработаны с помошью nlp_processor.
        content = ContentPydanticSchema(
            name="Default Name FROM TG",
            description="No description available",
            tags=["fdsf"],
            image=b"gg",
            contact={"link": " link"},
            date_start=datetime.now(),
            date_end=datetime.now(),
            time="00:00",
            location="Unknown",
            cost=0,
            city="nn",
        )

        # self.content_repo.save_content([content])
        # todo: тут идет вызов метода сохранения данных репозитория.
        return [content]


# todo: это пример того, как собрать этот юзкейс и запустить.
# gateway = TelegramGateway(client={})
# nlp_processor = NLPProcessor()
# tg_content_usecase = GetContentTgUseCase(gateway=gateway, nlp_processor=nlp_processor)
# data = tg_content_usecase.execute()
# print(data)
