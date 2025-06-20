from abc import ABC, abstractmethod


class AIProviderInterface(ABC):
    """
    Интерфейс для провайдеров AI сервисов.
    Определяет методы для работы с различными AI API.
    """

    @abstractmethod
    def send_request(self, prompt: str, **kwargs) -> str:
        """
        Отправляет запрос к AI API.

        Args:
            prompt: Текст промпта для AI
            **kwargs: Дополнительные параметры для запроса

        Returns:
            str: Ответ от AI сервиса
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Возвращает имя провайдера.

        Returns:
            str: Название провайдера
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Проверяет доступность провайдера.

        Returns:
            bool: True если провайдер доступен
        """
        pass
