import logging
from typing import Dict, Any, List

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)
from interface_adapters.gateways.ai_provider_base.ai_provider_interface import (
    AIProviderInterface,
)
from interface_adapters.gateways.prompt_processor_base.prompt_processor_interface import (
    PromptProcessorInterface,
)

logger = logging.getLogger("nlp_processor")


class NLPProcessor(NLPProcessorBase):
    """
    Рефакторированный класс для обработки NLP задач.
    Использует dependency injection для работы с различными провайдерами AI.
    """

    def __init__(
        self,
        ai_provider: AIProviderInterface,
        prompt_processor: PromptProcessorInterface,
    ) -> None:
        """
        Инициализирует NLPProcessor с переданными провайдерами.

        Args:
            ai_provider: Провайдер AI сервиса
            prompt_processor: Обработчик промптов
        """
        self.ai_provider = ai_provider
        self.prompt_processor = prompt_processor

        logger.debug(
            f"NLPProcessor инициализирован с провайдером: {self.ai_provider.get_provider_name()}"
        )

    def process(self, text: str) -> List[Dict[str, Any]]:
        """
        Главный метод: формирует промпт из main_prompt,
        вызывает AI провайдер, парсит JSON-ответ.
        Возвращает список словарей, каждый описывает событие.
        """
        if not self.ai_provider.is_available():
            logger.error(
                f"AI провайдер {self.ai_provider.get_provider_name()} недоступен"
            )
            return []

        main_prompt_template = self.prompt_processor.get_prompt_template("main_prompt")
        if not main_prompt_template:
            logger.error("Не найден шаблон main_prompt")
            return []

        context = self.prompt_processor.get_current_context()
        context["text"] = text

        prompt = self.prompt_processor.format_prompt(main_prompt_template, context)

        logger.debug(f"Отправляем запрос к {self.ai_provider.get_provider_name()}")
        raw_response = self.ai_provider.send_request(prompt)

        parsed_list = self.prompt_processor.parse_response(raw_response)
        logger.debug("Результат парсинга: %s объектов", len(parsed_list))
        return parsed_list

    def process_post(self, post: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Обрабатывает отдельный пост, выделяя text + image.
        Возвращает список событий (каждый – dict).
        """
        # Копируем, чтобы не портить исходный словарь
        post_copy = post.copy()

        image_data = post_copy.pop("image", None)
        text = post_copy.get("text", "")
        if not text:
            logger.info("Пост без текста – пропускаем.")
            return []

        logger.debug("Передаём в нейронку текст (длина=%s):\n%s", len(text), text)
        events = self.process(text)
        logger.debug("Нейронка вернула %s объектов", len(events))

        for evt in events:
            # Если нейронка не вложила 'image', подставляем наше
            if "image" not in evt or evt["image"] is None:
                evt["image"] = image_data
            # Объединяем прочие поля (channel, city, date и т.д.)
            evt.update(post_copy)

        return events

    def determine_category(
        self, event_text: str, service: str = "category_prompt"
    ) -> str:
        """
        Определяет категорию мероприятия.
        Сначала пытается использовать API, если не получается - возвращает пустую строку.
        """
        if not self.ai_provider.is_available():
            logger.warning(
                f"AI провайдер {self.ai_provider.get_provider_name()} недоступен"
            )
            return ""

        try:
            category_prompt_template = self.prompt_processor.get_prompt_template(
                service
            )
            if not category_prompt_template:
                logger.warning(f"Не найден шаблон промпта: {service}")
                return ""

            context = {"text": event_text}
            prompt = self.prompt_processor.format_prompt(
                category_prompt_template, context
            )

            result = self.ai_provider.send_request(prompt)
            if result and result.strip():
                return result.strip()
        except Exception as e:
            logger.warning(f"Ошибка при определении категории через API: {str(e)}")

        return ""

    def generate_link_title(self, event_text: str) -> str:
        """
        Генерирует название для ссылки.
        Использует шаблон link_title_prompt.
        Возвращает сгенерированное название как строку.
        """
        if not self.ai_provider.is_available():
            logger.warning(
                f"AI провайдер {self.ai_provider.get_provider_name()} недоступен"
            )
            return ""

        link_prompt_template = self.prompt_processor.get_prompt_template(
            "link_title_prompt"
        )
        if not link_prompt_template:
            logger.warning("Не найден шаблон link_title_prompt")
            return ""

        context = {"text": event_text}
        prompt = self.prompt_processor.format_prompt(link_prompt_template, context)

        result = self.ai_provider.send_request(prompt)
        return result if result else ""
