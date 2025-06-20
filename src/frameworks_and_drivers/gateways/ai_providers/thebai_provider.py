import os
import time
import logging
import requests

from interface_adapters.gateways.ai_provider_base.ai_provider_interface import (
    AIProviderInterface,
)

logger = logging.getLogger(__name__)


class ThebAIProvider(AIProviderInterface):
    """
    Провайдер для работы с ThebAI API.
    """

    def __init__(self, api_key: str = None, api_url: str = None):
        self.api_key = api_key or os.getenv(
            "THEBAI_API_KEY", "sk-te5U1TN6yvTYFuB8Nc8FVGhlQi5BSQL7dkdAaPePqRXNf7Wu"
        )
        self.api_url = api_url or os.getenv(
            "THEBAI_API_URL", "https://api.theb.ai/v1/chat/completions"
        )
        self.model = "theb-ai-4"
        self.max_retries = 3
        self.timeout = 30
        self.retry_delay = 5

    def send_request(self, prompt: str, **kwargs) -> str:
        """
        Отправляет запрос к ThebAI API.
        """
        logger.debug("Отправляем запрос к ThebAI API")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        # Применяем дополнительные параметры из kwargs
        payload.update(kwargs)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])

                if not choices:
                    logger.warning("ThebAI API вернул пустые choices.")
                    return ""

                content = choices[0]["message"]["content"]
                logger.debug("Ответ от ThebAI API получен успешно")
                return content

            except requests.Timeout:
                logger.warning(
                    f"Таймаут при запросе к ThebAI API (попытка {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

            except requests.RequestException as e:
                logger.error(f"Ошибка при запросе к ThebAI API: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                break

        logger.error("Все попытки запроса к ThebAI API завершились неудачно")
        return ""

    def get_provider_name(self) -> str:
        """
        Возвращает имя провайдера.
        """
        return "thebai"

    def is_available(self) -> bool:
        """
        Проверяет доступность провайдера.
        """
        return bool(self.api_key and self.api_url)
