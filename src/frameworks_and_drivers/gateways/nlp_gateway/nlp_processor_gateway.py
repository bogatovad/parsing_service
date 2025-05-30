from datetime import datetime
import json
import requests
import yaml
import logging
import os

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)

logging.basicConfig(level=logging.DEBUG)


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

        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_config = yaml.safe_load(f)

        logging.debug(
            "NLPProcessor инициализирован. Промпты загружены из: %s", prompt_file
        )

    def _parse_response(self, response_text: str) -> list:
        logging.debug("Парсим ответ нейросети: %s", response_text)
        if not response_text:
            return []
        if response_text.strip() == "[НЕ АФИША]":
            logging.debug("Ответ: [НЕ АФИША]. Вернём пустой список.")
            return []
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                logging.debug("Ответ не list и не dict.")
                return []
        except Exception as e:
            logging.error(f"Ошибка парсинга ответа: {e}")
            return []

    def _send_request(self, url, api_key, model, prompt):
        logging.debug("Отправляем запрос к API: %s, модель=%s", url, model)
        logging.debug("Промпт:\n%s", prompt)

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            choices = data.get("choices", [])
            if not choices:
                logging.warning("API вернул пустые choices.")
                return ""
            content = choices[0]["message"]["content"]
            logging.debug("Ответ API:\n%s", content)
            return content
        except Exception as e:
            logging.error(f"Ошибка при запросе к API: {e}")
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
        logging.debug("Результат парсинга: %s объектов", len(parsed_list))
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
            logging.info("Пост без текста – пропускаем.")
            return []

        logging.debug("Передаём в нейронку текст (длина=%s):\n%s", len(text), text)
        events = self.process(text)
        logging.debug("Нейронка вернула %s объектов", len(events))

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
        Использует шаблон category_prompt из YAML.
        Возвращает строку с категорией, полученную из API.
        """
        category_prompt_template = self.prompt_config.get(
            service, "Определи категорию: {text}"
        )
        prompt = category_prompt_template.format(text=event_text)
        result = self._call_api(prompt, service="thebai")
        return result

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
