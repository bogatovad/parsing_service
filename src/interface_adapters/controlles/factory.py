from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_gateway import (
    NLPProcessor,
)
from frameworks_and_drivers.gateways.parsing_gateway.kuda_go_gateway1 import (
    KudaGoGateway,
)
from frameworks_and_drivers.gateways.parsing_gateway.tg_gateway import TelegramGateway
from frameworks_and_drivers.gateways.parsing_gateway.timepad_gateway import (
    TimepadGateway,
)
from frameworks_and_drivers.gateways.parsing_gateway.yandex_afisha_gateway import (
    YandexAfishaGateway,
)
from frameworks_and_drivers.gateways.parsing_gateway.vk_gateway import (
    ParsingVK,
)
from usecases.kuda_go.kuda_go_usecase import GetContentKudaGoUseCase
from usecases.telegram.get_content_tg_usecase import GetContentTgUseCase
from usecases.timepad.timepad_usecase import GetContentTimepadUseCase
from usecases.yandex_afisha.yandex_afisha_usecase import GetContentYandexAfishaUseCase
from usecases.vk.vk_usecase import GetContentVkUseCase
from frameworks_and_drivers.repositories.content_repository import (
    ContentRepositoryProtocol,
)
from frameworks_and_drivers.repositories.file_repository import FileRepositoryProtocol


class UseCaseFactory:
    @staticmethod
    def get_tg_content_usecase() -> GetContentTgUseCase:
        return GetContentTgUseCase(
            gateway=TelegramGateway(),
            nlp_processor=NLPProcessor(),
            content_repo=ContentRepositoryProtocol(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_kuda_go_content_usecase() -> GetContentKudaGoUseCase:
        return GetContentKudaGoUseCase(
            gateway=KudaGoGateway(),
            nlp_processor=NLPProcessor(),
            content_repo=ContentRepositoryProtocol(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_yandex_afisha_content_usecase() -> GetContentYandexAfishaUseCase:
        return GetContentYandexAfishaUseCase(
            gateway=YandexAfishaGateway(),
            nlp_processor=NLPProcessor(),
            content_repo=ContentRepositoryProtocol(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_timepad_content_usecase() -> GetContentTimepadUseCase:
        return GetContentTimepadUseCase(
            gateway=TimepadGateway(),
            nlp_processor=NLPProcessor(),
            content_repo=ContentRepositoryProtocol(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_vk_content_usecase() -> GetContentVkUseCase:
        return GetContentVkUseCase(
            gateway=ParsingVK(),
            nlp_processor=NLPProcessor(),
            content_repo=ContentRepositoryProtocol(),
            file_repo=FileRepositoryProtocol(),
        )
