from datetime import datetime
import json
import requests
import yaml
import logging
import os

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import (
    NLPProcessorBase,
)

logging.basicConfig(level=logging.INFO)


class NLPProcessor(NLPProcessorBase):
    def __init__(self, prompt_file: str = "nlp_prompts.yaml") -> None:
        """
        Инициализирует NLPProcessor.
        Загружает конфигурацию (ключи API, число попыток, интервалы) из JSON-файла,
        а также промпты из YAML-файла.
        """

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

    def _parse_response(self, response_text: str) -> list:
        """
        Обрабатывает ответ от нейросети, предполагая, что он представляет собой валидный JSON-список.
        Если ответ равен "[НЕ АФИША]", возвращает пустой список.
        Если возвращен словарь, оборачивает его в список.
        Если парсинг не удаётся, сохраняет ответ в файл для отладки и возвращает пустой список.
        """
        try:
            if response_text.strip() == "[НЕ АФИША]":
                return []
            try:
                parsed = json.loads(response_text)
                print(f"{parsed=}")
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict):
                    return [parsed]
                else:
                    return []
            except Exception as e:
                logging.error(f"Ошибка парсинга ответа: {e}")
                return []
        except:  # noqa: E722
            return []

    def _send_request(self, url, api_key, model, prompt):
        """Отправляет запрос к API и обрабатывает ответ."""
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
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            response_data = response.json()
            choices = response_data.get("choices", [])

            if not choices:
                logging.warning("API вернул пустой список choices.")
                return []
            return choices[0]["message"]["content"]
        except:  # noqa: E722
            return []

    def _call_api(self, prompt: str, service: str = "thebai") -> list:
        """
        Унифицированный метод для вызова внешнего API с несколькими попытками.
        Если service == "thebai", обращается к основному сервису, иначе – к openrouter.
        Возвращает список словарей, полученных из API.
        """
        if service == "thebai":
            url, api_key, model = self.thebai_api_url, self.thebai_api_key, "theb-ai-4"
        else:
            url, api_key, model = (
                self.openrouter_api_url,
                self.openrouter_api_key,
                "anthropic/claude-3.5-sonnet",
            )
        result = self._send_request(url, api_key, model, prompt)
        return result

    def process(self, text: str) -> dict:
        """
        Основной метод обработки текста.
        Использует промпт main_prompt из YAML, подставляет в него текст и вызывает _call_api.
        Предполагается, что API вернет валидный JSON в виде списка.
        Возвращает список словарей, где каждый словарь описывает отдельное событие.
        """
        main_prompt_template = self.prompt_config.get("main_prompt", "")

        current_date = datetime.now().strftime("%Y-%m-%d")

        weekday_map = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье"
        }
        current_day = weekday_map[datetime.now().weekday()]
        
        prompt = (
            main_prompt_template
            .replace("{text}", text)
            .replace("{current_date}", current_date)
            .replace("{current_day}", current_day)
        )

        result_list = self._call_api(prompt, service="thebai")
        result_list = self._parse_response(result_list)
        if isinstance(result_list, list):
            return result_list
        return []

    def determine_category(self, event_text: str) -> str:
        """
        Определяет категорию мероприятия.
        Использует шаблон category_prompt из YAML.
        Возвращает строку с категорией, полученную из API.
        """
        category_prompt_template = self.prompt_config.get(
            "category_prompt", "Определи категорию: {text}"
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

    def process_post(self, post: dict) -> list:
        """
        Обрабатывает пост, отделяя текст для нейронки от поля с изображением.
        Передаёт текст в нейронку, а затем возвращает результат анализа вместе с данными изображения.
        Предполагается, что в посте есть ключ "text" для основного текста и (опционально) ключ "image" с байтами изображения.
        Возвращает список словарей – по одному на каждое событие, обнаруженное нейронкой.
        """
        post_copy = post.copy()
        image_data = post_copy.pop("image", None)
        text = post_copy.get("text", "")
        if not text:
            logging.info("Пост не содержит текста – пропускаем обработку.")
            return []

        analysis_results = self.process(text)

        for event in analysis_results:
            if "image" not in event or event.get("image") is None:
                event["image"] = image_data
            event.update(post_copy)

        return analysis_results
