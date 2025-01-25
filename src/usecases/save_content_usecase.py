from interface_adapters.presenters.schemas import ContentPydanticSchema
from interface_adapters.repositories.base_content_repository import ContentRepositoryProtocol
from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol
from usecases.common import AbstractUseCase


class SaveContentUseCase(AbstractUseCase):
    def __init__(self, content_repository: ContentRepositoryProtocol, file_repository: FileRepositoryProtocol) -> None:
        self.content_repository = content_repository
        self.file_repository = file_repository

    def execute(self, content: ContentPydanticSchema) -> bool:
        if self.content_repository.save(content):
            return self.file_repository.save_file(b"file_data_placeholder")
        return False
