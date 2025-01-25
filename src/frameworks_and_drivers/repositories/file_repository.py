from interface_adapters.repositories.base_file_repository import FileRepositoryProtocol


class FileRepositoryProtocol(FileRepositoryProtocol):
    def upload_file(self, filename: str, content: bytes) -> None:
        """
        Метод для загрузки файла.

        :param filename: Имя файла.
        :param content: Данные файла в виде байтов.
        """
        return []
