from abc import abstractmethod, ABC


class BaseGateway(ABC):
    def __init__(self, client=None) -> None:
        self.client = client

    @abstractmethod
    def fetch_content(self) -> list[dict]:
        raise NotImplementedError
<<<<<<< HEAD
    
    def get_sources(self) -> list:
        raise NotImplementedError 
=======

    @abstractmethod
    def get_sources(self):
        raise NotImplementedError
>>>>>>> dbe7ebfad1960b4eed12b5666c5c86f8c7620f76
