from datetime import datetime
import json
import requests
import yaml
import logging
import os
from pathlib import Path
import time

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)

logger = logging.getLogger("nlp_processor")


class NLPProcessor(NLPProcessorBase):
    """
    Класс, отвечающий за вызов LLM (theb.ai / openrouter),
    формирование промптов и разбор ответа в список событий.
    """

    def __init__(self, prompt_file: str = "nlp_prompts.yaml") -> None:
        self.thebai_api_url = os.getenv(
            "THEBAI_API_URL", "https://api.theb.ai/v1/chat/completions"
        )
        self.thebai_api_key = "sk-te5U1TN6yvTYFuB8Nc8FVGhlQi5BSQL7dkdAaPePqRXNf7Wu"
        self.openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_api_key = (
            "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"
        )
        self.attempt_interval = 60
        self.max_retries = 3

        # Определяем путь к файлу относительно корня проекта
        project_root = (
            Path(__file__).resolve().parents[4]
        )  # 4 уровня вверх до корня проекта
        prompt_file_path = project_root / prompt_file

        with open(prompt_file_path, "r", encoding="utf-8") as f:
            self.prompt_config = yaml.safe_load(f)

        logger.debug(
            "NLPProcessor инициализирован. Промпты загружены из: %s", prompt_file_path
        )

    def _parse_response(self, response_text: str) -> list:
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

    def _send_request(self, url, api_key, model, prompt):
        logger.debug("Отправляем запрос к API: %s, модель=%s", url, model)
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        max_retries = 3
        timeout = 30
        retry_delay = 5

        for attempt in range(max_retries):
            try:
                resp = requests.post(
                    url, headers=headers, json=payload, timeout=timeout
                )
                resp.raise_for_status()
                data = resp.json()
                choices = data.get("choices", [])

                if not choices:
                    logger.warning("API вернул пустые choices.")
                    return ""

                content = choices[0]["message"]["content"]
                logger.debug("Ответ API получен успешно")
                return content
            except requests.Timeout:
                logger.error(f"Ответ от модели {resp.json()}")
                logger.warning(
                    f"Таймаут при запросе к API (попытка {attempt + 1}/{max_retries})"
                )
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
            except requests.RequestException as e:
                logger.error(f"Ошибка при запросе к API: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                break

        logger.error("Все попытки запроса к API завершились неудачно")
        return ""

    def _call_api(self, prompt: str, service: str = "thebai") -> str:
        """
        Унифицированный метод запроса:
        service == 'thebai' => theb.ai
        иначе openrouter.
        """
        if service == "thebai":
            url, api_key, model = self.thebai_api_url, self.thebai_api_key, "theb-ai-4"
        else:
            url, api_key, model = (
                self.openrouter_api_url,
                self.openrouter_api_key,
                "anthropic/claude-3.5-sonnet",
            )

        return self._send_request(url, api_key, model, prompt)

    def process(self, text: str) -> list:
        """
        Главный метод: формирует промпт из main_prompt,
        вызывает _call_api, парсит JSON-ответ.
        Возвращает список словарей, каждый описывает событие.
        """
        main_prompt = self.prompt_config.get("main_prompt", "")
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

        prompt = (
            main_prompt.replace("{text}", text)
            .replace("{current_date}", current_date)
            .replace("{current_day}", current_day)
        )

        raw_response = self._call_api(prompt, service="thebai")
        parsed_list = self._parse_response(raw_response)
        logger.debug("Результат парсинга: %s объектов", len(parsed_list))
        return parsed_list

    def process_post(self, post: dict) -> list:
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
        Сначала пытается использовать API, если не получается - использует локальные правила.
        """
        try:
            # Пробуем через API
            category_prompt_template = self.prompt_config.get(
                service, "Определи категорию: {text}"
            )
            prompt = category_prompt_template.format(text=event_text)
            result = self._call_api(prompt, service="thebai")
            if result and result.strip():
                return result.strip()
        except Exception as e:
            logger.warning(f"Ошибка при определении категории через API: {str(e)}")

        # Если API не сработал, используем локальные правила
        text = event_text.lower()

        # Правила определения категории
        if any(word in text for word in ["концерт", "музыка", "опера", "джаз", "рок"]):
            return "Музыка"
        elif any(word in text for word in ["театр", "спектакль", "драма", "комедия"]):
            return "Театр"
        elif any(word in text for word in ["выставка", "галерея", "искусство"]):
            return "Искусство"
        elif any(word in text for word in ["лекция", "семинар", "мастер-класс"]):
            return "Образование"
        elif any(word in text for word in ["кино", "фильм", "премьера"]):
            return "Кино"
        elif any(word in text for word in ["дети", "ребенок", "семья"]):
            return "Семья"
        elif any(word in text for word in ["экскурсия", "прогулка", "тур"]):
            return "Экскурсия"
        elif any(word in text for word in ["it", "программирование", "разработка"]):
            return "IT-Ивенты"
        elif any(word in text for word in ["стендап", "юмор", "комик"]):
            return "StandUp"
        elif any(word in text for word in ["еда", "кулинария", "гастрономия"]):
            return "Еда"
        elif any(word in text for word in ["спорт", "фитнес", "тренировка"]):
            return "Спорт"

        return "Разное"

    def generate_link_title(self, event_text: str) -> str:
        """
        Генерирует название для ссылки.
        Использует шаблон link_title_prompt из YAML.
        Возвращает сгенерированное название как строку.
        """
        link_prompt_template = self.prompt_config.get(
            "link_title_prompt", "Придумай название для ссылки: {text}"
        )
        prompt = link_prompt_template.format(text=event_text)
        result = self._call_api(prompt, service="thebai")
        return result
