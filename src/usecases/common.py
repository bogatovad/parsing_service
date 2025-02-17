from typing import Any
from abc import ABC, abstractmethod

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from interface_adapters.repositories.base_content_repository import (
    ContentRepositoryProtocol,
)


class AbstractUseCase(ABC):
    def __init__(
        self,
        gateway: BaseGateway,
        nlp_processor: NLPProcessorBase,
        content_repo: ContentRepositoryProtocol,
        file_repo: FileRepositoryProtocol,
    ) -> None:
        self.gateway = gateway
        self.nlp_processor = nlp_processor

    @abstractmethod
    def execute(self, *args, **kwargs) -> Any:
        raise NotImplementedError
