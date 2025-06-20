from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_factory import (
    NLPProcessorFactory,
)
from frameworks_and_drivers.gateways.parsing_gateway.kuda_go_gateway1 import (
    KudaGoGateway,
)
from frameworks_and_drivers.gateways.parsing_gateway.tg_gateway import TelegramGateway
from frameworks_and_drivers.gateways.parsing_gateway.timepad_gateway import (
    TimepadGateway,
)
from frameworks_and_drivers.gateways.parsing_gateway.vk_gateway import (
    ParsingVK,
)
from usecases.kuda_go.kuda_go_usecase import GetContentKudaGoUseCase
from usecases.telegram.get_content_tg_usecase import GetContentTgUseCase
from usecases.timepad.timepad_usecase import GetContentTimepadUseCase
from usecases.vk.vk_usecase import GetContentVkUseCase
from usecases.places.run_places_usecase import GetPlacesUsecase
from frameworks_and_drivers.repositories.content_repository import (
    DjangoContentRepository,
)
from frameworks_and_drivers.repositories.file_repository import FileRepositoryProtocol


class UseCaseFactory:
    @staticmethod
    def get_tg_content_usecase(ai_provider: str = "openrouter") -> GetContentTgUseCase:
        """
        Создает use case для Telegram с выбранным AI провайдером.

        Args:
            ai_provider: Имя AI провайдера ("thebai", "openrouter")
        """
        return GetContentTgUseCase(
            gateway=TelegramGateway(),
            nlp_processor=NLPProcessorFactory.create_nlp_processor(
                provider_name=ai_provider
            ),
            content_repo=DjangoContentRepository(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_kuda_go_content_usecase(
        ai_provider: str = "openrouter",
    ) -> GetContentKudaGoUseCase:
        """
        Создает use case для KudaGo с выбранным AI провайдером.

        Args:
            ai_provider: Имя AI провайдера ("thebai", "openrouter")
        """
        return GetContentKudaGoUseCase(
            gateway=KudaGoGateway(),
            nlp_processor=NLPProcessorFactory.create_nlp_processor(
                provider_name=ai_provider
            ),
            content_repo=DjangoContentRepository(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_timepad_content_usecase(
        ai_provider: str = "openrouter",
    ) -> GetContentTimepadUseCase:
        """
        Создает use case для Timepad с выбранным AI провайдером.

        Args:
            ai_provider: Имя AI провайдера ("thebai", "openrouter")
        """
        return GetContentTimepadUseCase(
            gateway=TimepadGateway(),
            nlp_processor=NLPProcessorFactory.create_nlp_processor(
                provider_name=ai_provider
            ),
            content_repo=DjangoContentRepository(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_vk_content_usecase(ai_provider: str = "openrouter") -> GetContentVkUseCase:
        """
        Создает use case для VK с выбранным AI провайдером.

        Args:
            ai_provider: Имя AI провайдера ("thebai", "openrouter")
        """
        return GetContentVkUseCase(
            gateway=ParsingVK(),
            nlp_processor=NLPProcessorFactory.create_nlp_processor(
                provider_name=ai_provider
            ),
            content_repo=DjangoContentRepository(),
            file_repo=FileRepositoryProtocol(),
        )

    @staticmethod
    def get_place_content_usecase(ai_provider: str = "openrouter") -> GetPlacesUsecase:
        """
        Создает use case для Places с выбранным AI провайдером.

        Args:
            ai_provider: Имя AI провайдера ("thebai", "openrouter")
        """
        return GetPlacesUsecase(
            gateway=ParsingVK(),
            nlp_processor=NLPProcessorFactory.create_nlp_processor(
                provider_name=ai_provider
            ),
            content_repo=DjangoContentRepository(),
            file_repo=FileRepositoryProtocol(),
        )
