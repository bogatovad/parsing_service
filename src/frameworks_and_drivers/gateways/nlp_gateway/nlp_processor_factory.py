from typing import Optional, Dict, Any
import logging

from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_gateway import (
    NLPProcessor,
)
from frameworks_and_drivers.gateways.ai_providers.thebai_provider import ThebAIProvider
from frameworks_and_drivers.gateways.ai_providers.openrouter_provider import (
    OpenRouterProvider,
)
from frameworks_and_drivers.gateways.prompt_processors.yaml_prompt_processor import (
    YamlPromptProcessor,
)
from interface_adapters.gateways.ai_provider_base.ai_provider_interface import (
    AIProviderInterface,
)
from interface_adapters.gateways.prompt_processor_base.prompt_processor_interface import (
    PromptProcessorInterface,
)

logger = logging.getLogger(__name__)


class NLPProcessorFactory:
    """
    Фабрика для создания экземпляров NLPProcessor с различными провайдерами.
    Обеспечивает гибкость в выборе AI провайдера и обработчика промптов.
    """

    # Зарегистрированные провайдеры
    PROVIDERS = {
        "thebai": ThebAIProvider,
        "openrouter": OpenRouterProvider,
    }

    # Зарегистрированные обработчики промптов
    PROMPT_PROCESSORS = {
        "yaml": YamlPromptProcessor,
    }

    @classmethod
    def create_nlp_processor(
        self,
        provider_name: str = "openrouter",
        prompt_processor_name: str = "yaml",
        provider_config: Optional[Dict[str, Any]] = None,
        prompt_processor_config: Optional[Dict[str, Any]] = None,
    ) -> NLPProcessor:
        """
        Создает экземпляр NLPProcessor с указанными провайдерами.

        Args:
            provider_name: Имя AI провайдера ("thebai", "openrouter")
            prompt_processor_name: Имя обработчика промптов ("yaml")
            provider_config: Конфигурация для AI провайдера
            prompt_processor_config: Конфигурация для обработчика промптов

        Returns:
            NLPProcessor: Настроенный экземпляр NLPProcessor

        Raises:
            ValueError: Если указанный провайдер или обработчик не найден
        """
        # Создаем AI провайдер
        if provider_name not in self.PROVIDERS:
            raise ValueError(
                f"Неизвестный провайдер: {provider_name}. Доступные: {list(self.PROVIDERS.keys())}"
            )

        provider_class = self.PROVIDERS[provider_name]
        provider_config = provider_config or {}
        ai_provider = provider_class(**provider_config)

        # Создаем обработчик промптов
        if prompt_processor_name not in self.PROMPT_PROCESSORS:
            raise ValueError(
                f"Неизвестный обработчик промптов: {prompt_processor_name}. "
                f"Доступные: {list(self.PROMPT_PROCESSORS.keys())}"
            )

        processor_class = self.PROMPT_PROCESSORS[prompt_processor_name]
        prompt_processor_config = prompt_processor_config or {}
        prompt_processor = processor_class(**prompt_processor_config)

        logger.info(
            f"Создан NLPProcessor с провайдером: {provider_name}, обработчиком промптов: {prompt_processor_name}"
        )

        return NLPProcessor(ai_provider, prompt_processor)

    @classmethod
    def create_with_custom_providers(
        self,
        ai_provider: AIProviderInterface,
        prompt_processor: PromptProcessorInterface,
    ) -> NLPProcessor:
        """
        Создает экземпляр NLPProcessor с пользовательскими провайдерами.

        Args:
            ai_provider: Пользовательский AI провайдер
            prompt_processor: Пользовательский обработчик промптов

        Returns:
            NLPProcessor: Настроенный экземпляр NLPProcessor
        """
        logger.info(
            f"Создан NLPProcessor с пользовательскими провайдерами: {ai_provider.get_provider_name()}"
        )
        return NLPProcessor(ai_provider, prompt_processor)

    @classmethod
    def register_provider(self, name: str, provider_class: type):
        """
        Регистрирует новый AI провайдер.

        Args:
            name: Имя провайдера
            provider_class: Класс провайдера
        """
        self.PROVIDERS[name] = provider_class
        logger.info(f"Зарегистрирован новый провайдер: {name}")

    @classmethod
    def register_prompt_processor(self, name: str, processor_class: type):
        """
        Регистрирует новый обработчик промптов.

        Args:
            name: Имя обработчика
            processor_class: Класс обработчика
        """
        self.PROMPT_PROCESSORS[name] = processor_class
        logger.info(f"Зарегистрирован новый обработчик промптов: {name}")

    @classmethod
    def list_available_providers(self) -> list:
        """
        Возвращает список доступных AI провайдеров.

        Returns:
            list: Список имен провайдеров
        """
        return list(self.PROVIDERS.keys())

    @classmethod
    def list_available_prompt_processors(self) -> list:
        """
        Возвращает список доступных обработчиков промптов.

        Returns:
            list: Список имен обработчиков
        """
        return list(self.PROMPT_PROCESSORS.keys())
