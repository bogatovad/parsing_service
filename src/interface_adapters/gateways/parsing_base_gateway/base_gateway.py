from abc import abstractmethod, ABC


class BaseGateway(ABC):
    def __init__(self, client=None) -> None:
        self.client = client

    @abstractmethod
    def fetch_content(self) -> list[dict]:
        raise NotImplementedError
