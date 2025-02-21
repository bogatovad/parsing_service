from abc import ABC, abstractmethod


class NLPProcessorBase(ABC):
    def __init__(self, *args, **kwargs) -> None:
        """
        Конструктор для инициализации NLPProcessorBase.
        Параметры могут быть переданы в зависимости от реализации.
        """
        raise NotImplementedError

    @abstractmethod
    def process(self, *args, **kwargs) -> dict:
        raise NotImplementedError

    def generate_link_title(self) -> str:
        raise NotImplementedError

    def determine_category(self) -> str:
        raise NotImplementedError

    def process_post(self, post: dict) -> list:
        raise NotImplementedError
