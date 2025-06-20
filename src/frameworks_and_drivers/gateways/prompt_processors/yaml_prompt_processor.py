import json
import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from interface_adapters.gateways.prompt_processor_base.prompt_processor_interface import (
    PromptProcessorInterface,
)

logger = logging.getLogger(__name__)


class YamlPromptProcessor(PromptProcessorInterface):
    """
    Обработчик промптов, который работает с YAML конфигурацией.
    """

    def __init__(self, prompt_file: str = "nlp_prompts.yaml"):
        # Определяем путь к файлу относительно корня проекта
        project_root = (
            Path(__file__).resolve().parents[4]
        )  # 4 уровня вверх до корня проекта
        prompt_file_path = project_root / prompt_file

        with open(prompt_file_path, "r", encoding="utf-8") as f:
            self.prompt_config = yaml.safe_load(f)

        logger.debug(
            "YamlPromptProcessor инициализирован. Промпты загружены из: %s",
            prompt_file_path,
        )

    def format_prompt(self, template: str, context: Dict[str, Any]) -> str:
        """
        Форматирует промпт с использованием шаблона и контекста.
        """
        formatted_prompt = template
        for key, value in context.items():
            placeholder = "{" + key + "}"
            formatted_prompt = formatted_prompt.replace(placeholder, str(value))
        return formatted_prompt

    def parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Парсит ответ от AI сервиса.
        """
        logger.debug("Парсим ответ нейросети: %s", response_text)

        if not response_text:
            return []

        if response_text.strip() == "[НЕ АФИША]":
            logger.debug("Ответ: [НЕ АФИША]. Вернём пустой список.")
            return []

        try:
            parsed = json.loads(response_text)

            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                logger.debug("Ответ не list и не dict.")
                return []
        except Exception as e:
            logger.error(f"Ошибка парсинга ответа: {e}")
            return []

    def get_current_context(self) -> Dict[str, Any]:
        """
        Получает текущий контекст для промптов.
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        weekday_map = [
            "Понедельник",
            "Вторник",
            "Среда",
            "Четверг",
            "Пятница",
            "Суббота",
            "Воскресенье",
        ]
        current_day = weekday_map[datetime.now().weekday()]

        return {
            "current_date": current_date,
            "current_day": current_day,
        }

    def get_prompt_template(self, prompt_name: str) -> str:
        """
        Получает шаблон промпта по имени.
        """
        return self.prompt_config.get(prompt_name, "")
