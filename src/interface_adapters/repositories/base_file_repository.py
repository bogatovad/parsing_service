from abc import abstractmethod, ABC


class FileRepositoryProtocol(ABC):
    @abstractmethod
    def upload_file(self, filename: str, content: bytes) -> None:
        """
        Метод для загрузки файла.

        :param filename: Имя файла.
        :param content: Данные файла в виде байтов.
        """
        raise NotImplementedError
