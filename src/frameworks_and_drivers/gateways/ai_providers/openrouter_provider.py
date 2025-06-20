import os
import time
import logging
import requests

from interface_adapters.gateways.ai_provider_base.ai_provider_interface import (
    AIProviderInterface,
)

logger = logging.getLogger(__name__)


class OpenRouterProvider(AIProviderInterface):
    """
    Провайдер для работы с OpenRouter API.
    """

    def __init__(self, api_key: str = None, api_url: str = None, model: str = None):
        self.api_key = api_key or os.getenv(
            "OPENROUTER_API_KEY",
            "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",
        )
        self.api_url = api_url or "https://openrouter.ai/api/v1/chat/completions"
        self.model = model or "openai/gpt-3.5-turbo"
        self.max_retries = 3
        self.timeout = 30
        self.retry_delay = 5

    def send_request(self, prompt: str, **kwargs) -> str:
        """
        Отправляет запрос к OpenRouter API.
        """
        logger.debug("Отправляем запрос к OpenRouter API")

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
                    logger.warning("OpenRouter API вернул пустые choices.")
                    return ""

                content = choices[0]["message"]["content"]
                logger.debug("Ответ от OpenRouter API получен успешно")
                return content

            except requests.Timeout:
                logger.warning(
                    f"Таймаут при запросе к OpenRouter API (попытка {attempt + 1}/{self.max_retries})"
                )
                if response:
                    try:
                        logger.error(f"Ответ от модели {response.json()}")
                    except:  # noqa: E722
                        pass

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

            except requests.RequestException as e:
                if response:
                    try:
                        logger.error(f"Ответ от модели {response.json()}")
                    except:  # noqa: E722
                        pass

                logger.error(f"Ошибка при запросе к OpenRouter API: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                break

        logger.error("Все попытки запроса к OpenRouter API завершились неудачно")
        return ""

    def get_provider_name(self) -> str:
        """
        Возвращает имя провайдера.
        """
        return "openrouter"

    def is_available(self) -> bool:
        """
        Проверяет доступность провайдера.
        """
        return bool(self.api_key and self.api_url)
