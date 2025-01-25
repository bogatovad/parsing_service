from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_gateway import NLPProcessor
from frameworks_and_drivers.gateways.parsing_gateway.kuda_go_gateway import KudaGoGateway
from frameworks_and_drivers.gateways.parsing_gateway.tg_gateway import TelegramGateway
from frameworks_and_drivers.gateways.parsing_gateway.yandex_afisha_gateway import YandexAfishaGateway
from usecases.kuda_go.kuda_go_usecase import GetContentKudaGoUseCase
from usecases.telegram.get_content_tg_usecase import GetContentTgUseCase
from usecases.yandex_afisha.yandex_afisha_usecase import GetContentYandexAfishaUseCase


class UseCaseFactory:
    @staticmethod
    def get_tg_content_usecase() -> GetContentTgUseCase:
        return GetContentTgUseCase(
            gateway=TelegramGateway(),
            nlp_processor=NLPProcessor()
        )

    @staticmethod
    def get_kuda_go_content_usecase() -> GetContentKudaGoUseCase:
        return GetContentKudaGoUseCase(
            gateway=KudaGoGateway(),
            nlp_processor=NLPProcessor()
        )

    @staticmethod
    def get_yandex_afisha_content_usecase() -> GetContentYandexAfishaUseCase:
        return GetContentYandexAfishaUseCase(
            gateway=YandexAfishaGateway(),
            nlp_processor=NLPProcessor()
        )
