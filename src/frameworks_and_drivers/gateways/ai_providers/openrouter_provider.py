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

        # Приоритет выбора модели:
        # 1. Параметр конструктора
        # 2. Переменная окружения OPENROUTER_MODEL
        # 3. Значение по умолчанию
        self.model = model or os.getenv("OPENROUTER_MODEL") or "openai/gpt-3.5-turbo"

        self.max_retries = 3
        self.timeout = 30
        self.retry_delay = 5
        self.rate_limit_delay = (
            2  # Задержка между запросами для избежания rate limiting
        )
        self._consecutive_errors = 0  # Счетчик последовательных ошибок

        logger.debug(f"OpenRouterProvider инициализирован с моделью: {self.model}")

    def send_request(self, prompt: str, **kwargs) -> str:
        """
        Отправляет запрос к OpenRouter API с улучшенной обработкой ошибок.
        """
        # Добавляем небольшую задержку между запросами для избежания rate limiting
        if self._consecutive_errors > 0:
            delay = min(
                self.rate_limit_delay * self._consecutive_errors, 10
            )  # Максимум 10 секунд
            logger.debug(f"Добавляем задержку {delay}с из-за предыдущих ошибок")
            time.sleep(delay)

        logger.debug(f"Отправляем запрос к OpenRouter API с моделью: {self.model}")

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
            "HTTP-Referer": "https://your-app.com",  # Некоторые API требуют referer
            "X-Title": "NLP Parser Service",  # Идентификация приложения
        }

        for attempt in range(self.max_retries):
            try:
                response = requests.post(
                    self.api_url, headers=headers, json=payload, timeout=self.timeout
                )

                # Логируем статус код для отладки
                logger.debug(
                    f"OpenRouter API ответил со статусом: {response.status_code}"
                )

                if response.status_code == 403:
                    self._consecutive_errors += 1
                    logger.error(
                        f"OpenRouter API вернул 403 Forbidden (ошибка #{self._consecutive_errors})"
                    )
                    logger.error(f"Модель: {self.model}")

                    try:
                        error_details = response.json()
                        logger.error(f"Детали ошибки: {error_details}")

                        # Проверяем конкретную причину ошибки
                        if "error" in error_details:
                            error_msg = error_details["error"]
                            if isinstance(error_msg, dict):
                                error_msg = error_msg.get("message", str(error_msg))
                            logger.error(f"Сообщение об ошибке: {error_msg}")

                    except:  # noqa: E722
                        logger.error(f"Ответ сервера: {response.text}")

                    # Выводим рекомендации по решению проблемы
                    self._log_403_recommendations()

                    # Для 403 увеличиваем задержку экспоненциально
                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (
                            2**attempt
                        )  # Экспоненциальная задержка
                        logger.warning(
                            f"403 ошибка, ждём {delay} секунд перед повтором (попытка {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(delay)
                        continue
                    else:
                        logger.error("Все попытки обхода 403 ошибки исчерпаны")
                        return ""

                elif response.status_code == 429:
                    self._consecutive_errors += 1
                    logger.warning("OpenRouter API вернул 429 Too Many Requests")
                    try:
                        error_details = response.json()
                        logger.warning(f"Rate limit детали: {error_details}")
                    except:  # noqa: E722
                        pass

                    if attempt < self.max_retries - 1:
                        delay = self.retry_delay * (
                            2**attempt
                        )  # Экспоненциальная задержка
                        logger.warning(
                            f"Rate limit, ждём {delay} секунд (попытка {attempt + 1}/{self.max_retries})"
                        )
                        time.sleep(delay)
                        continue

                response.raise_for_status()
                data = response.json()
                choices = data.get("choices", [])

                if not choices:
                    logger.warning("OpenRouter API вернул пустые choices.")
                    return ""

                content = choices[0]["message"]["content"]
                logger.debug("Ответ от OpenRouter API получен успешно")

                # Сбрасываем счетчик ошибок при успешном запросе
                self._consecutive_errors = 0

                return content

            except requests.Timeout:
                self._consecutive_errors += 1
                logger.warning(
                    f"Таймаут при запросе к OpenRouter API (попытка {attempt + 1}/{self.max_retries})"
                )
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue

            except requests.RequestException as e:
                self._consecutive_errors += 1
                logger.error(f"Ошибка при запросе к OpenRouter API: {e}")

                # Пытаемся получить детали ошибки
                if hasattr(e, "response") and e.response is not None:
                    try:
                        error_details = e.response.json()
                        logger.error(f"Детали ошибки API: {error_details}")
                    except:  # noqa: E722
                        logger.error(f"Ответ сервера: {e.response.text}")

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                break

        logger.error("Все попытки запроса к OpenRouter API завершились неудачно")
        return ""

    def _log_403_recommendations(self):
        """
        Выводит рекомендации по решению проблем с 403 ошибками.
        """
        logger.error("═══ РЕКОМЕНДАЦИИ ПО РЕШЕНИЮ 403 ОШИБКИ ═══")
        logger.error("1. Проверьте API ключ:")
        logger.error("   - Убедитесь, что ключ действительный")
        logger.error("   - Проверьте, не истек ли срок действия")
        logger.error("   - Убедитесь, что ключ имеет необходимые права")
        logger.error("2. Проверьте лимиты:")
        logger.error("   - Возможно, превышен дневной лимит запросов")
        logger.error("   - Проверьте баланс на аккаунте OpenRouter")
        logger.error(f"3. Текущая модель: {self.model}")
        logger.error(
            "   - Попробуйте бесплатную модель: meta-llama/llama-3.1-8b-instruct:free"
        )
        logger.error(
            "   - Установите переменную: export OPENROUTER_MODEL='meta-llama/llama-3.1-8b-instruct:free'"
        )
        logger.error(
            "4. Проверьте статус OpenRouter API на https://status.openrouter.ai/"
        )
        logger.error("═══════════════════════════════════════════")

    def get_provider_name(self) -> str:
        """
        Возвращает имя провайдера.
        """
        return "openrouter"

    def is_available(self) -> bool:
        """
        Проверяет доступность провайдера.
        """
        available = bool(self.api_key and self.api_url)
        if not available:
            logger.warning(
                "OpenRouter провайдер недоступен: отсутствует API ключ или URL"
            )
        return available

    def get_error_count(self) -> int:
        """
        Возвращает количество последовательных ошибок.
        """
        return self._consecutive_errors

    def reset_error_count(self):
        """
        Сбрасывает счетчик ошибок.
        """
        self._consecutive_errors = 0

    def get_current_model(self) -> str:
        """
        Возвращает текущую используемую модель.
        """
        return self.model
