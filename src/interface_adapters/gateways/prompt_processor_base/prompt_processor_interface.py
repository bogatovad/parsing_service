from abc import ABC, abstractmethod
from typing import Dict, Any, List


class PromptProcessorInterface(ABC):
    """
    Интерфейс для обработки промптов.
    Отвечает за формирование промптов и парсинг ответов от AI.
    """

    @abstractmethod
    def format_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """
        Форматирует промпт с использованием шаблона и контекста.

        Args:
            template: Шаблон промпта
            context: Контекст для подстановки в шаблон

        Returns:
            str: Отформатированный промпт
        """
        pass

    @abstractmethod
    def parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Парсит ответ от AI сервиса.

        Args:
            response_text: Ответ от AI сервиса

        Returns:
            List[Dict[str, Any]]: Список распарсенных объектов
        """
        pass

    @abstractmethod
    def get_current_context(self) -> Dict[str, Any]:
        """
        Получает текущий контекст для промптов (дата, день недели и т.д.).

        Returns:
            Dict[str, Any]: Словарь с контекстными данными
        """
        pass

    @abstractmethod
    def get_prompt_template(self, prompt_name: str) -> str:
        """
        Получает шаблон промпта по имени.

        Args:
            prompt_name: Имя промпта

        Returns:
            str: Шаблон промпта
        """
        pass
