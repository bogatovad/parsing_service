import json
import time
import requests
import yaml
import logging
import os

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase

logging.basicConfig(level=logging.INFO)


class NLPProcessor(NLPProcessorBase):
    def __init__(self, prompt_file: str = "nlp_prompts.yaml") -> None:
        """
        Инициализирует NLPProcessor.
        Загружает конфигурацию (ключи API, число попыток, интервалы) из JSON-файла,
        а также промпты из YAML-файла.
        """

        self.thebai_api_url = os.getenv("THEBAI_API_URL", "https://api.thebai.ru/v1/chat/completions")
        self.thebai_api_key = "sk-te5U1TN6yvTYFuB8Nc8FVGhlQi5BSQL7dkdAaPePqRXNf7Wu"
        self.openrouter_api_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_api_key = "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"
        self.attempts = 3
        self.attempt_interval = 60

        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_config = yaml.safe_load(f)

    def _parse_response(self, response_text: str) -> list:
        """
        Обрабатывает ответ от нейросети, предполагая, что он представляет собой валидный JSON-список.
        Если ответ равен "[НЕ АФИША]", возвращает пустой список.
        Если возвращен словарь, оборачивает его в список.
        Если парсинг не удаётся, сохраняет ответ в файл для отладки и возвращает пустой список.
        """
        if response_text.strip() == "[НЕ АФИША]":
            return []
        try:
            parsed = json.loads(response_text)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict):
                return [parsed]
            else:
                return []
        except Exception as e:
            logging.error(f"Ошибка парсинга ответа: {e}")
            return []

    def _call_api(self, prompt: str, service: str = "thebai") -> list:
        """
        Унифицированный метод для вызова внешнего API с несколькими попытками.
        Если service == "thebai", обращается к основному сервису, иначе – к openrouter.
        Возвращает список словарей, полученных из API.
        """
        if service == "thebai":
            url = self.thebai_api_url
            api_key = self.thebai_api_key
            model = "theb-ai-4"
        else:
            url = self.openrouter_api_url
            api_key = self.openrouter_api_key
            model = "anthropic/claude-3.5-sonnet"

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        for attempt in range(1, self.attempts + 1):
            try:
                logging.info(f"Попытка {attempt}: отправляем запрос к {service}.")
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                response_data = response.json()
                content = response_data["choices"][0]["message"]["content"]
                logging.info(f"Ответ от {service}: {content}")
                return self._parse_response(content)
            except requests.exceptions.RequestException as e:
                logging.error(f"Ошибка запроса к {service} (попытка {attempt}): {e}")
                if attempt < self.attempts:
                    logging.info(f"Ожидание {self.attempt_interval} секунд перед повтором...")
                    time.sleep(self.attempt_interval)
                else:
                    logging.info(f"Не удалось получить ответ от {service}.")
                    break
            except Exception as e:
                logging.error(f"Непредвиденная ошибка при вызове {service}: {e}")
                break

        if service == "thebai":
            logging.info("Переключение на сервис OpenRouter.")
            return self._call_api(prompt, service="openrouter")
        return []

    def process(self, text: str) -> list:
        """
        Основной метод обработки текста.
        Использует промпт main_prompt из YAML, подставляет в него текст и вызывает _call_api.
        Предполагается, что API вернет валидный JSON в виде списка.
        Возвращает список словарей, где каждый словарь описывает отдельное событие.
        """
        main_prompt_template = self.prompt_config.get("main_prompt", "")
        prompt = main_prompt_template.format(text=text)
        result_list = self._call_api(prompt, service="thebai")
        if isinstance(result_list, list):
            return result_list
        return []

    def determine_category(self, event_text: str) -> str:
        """
        Определяет категорию мероприятия.
        Использует шаблон category_prompt из YAML.
        Возвращает строку с категорией, полученную из API.
        """
        category_prompt_template = self.prompt_config.get("category_prompt", "Определи категорию: {text}")
        prompt = category_prompt_template.format(text=event_text)
        result_list = self._call_api(prompt, service="thebai")
        if result_list:
            return str(result_list[0]).strip()
        return ""

    def generate_link_title(self, event_text: str) -> str:
        """
        Генерирует название для ссылки.
        Использует шаблон link_title_prompt из YAML.
        Возвращает сгенерированное название как строку.
        """
        link_prompt_template = self.prompt_config.get("link_title_prompt", "Придумай название для ссылки: {text}")
        prompt = link_prompt_template.format(text=event_text)
        result_list = self._call_api(prompt, service="thebai")
        if result_list:
            return str(result_list[0]).strip()
        return ""

    def process_post(self, post: dict) -> list:
        """
        Обрабатывает пост, отделяя текст для нейронки от поля с изображением.
        Передаёт текст в нейронку, а затем возвращает результат анализа вместе с данными изображения.
        Предполагается, что в посте есть ключ "text" для основного текста и (опционально) ключ "image" с байтами изображения.
        Возвращает список словарей – по одному на каждое событие, обнаруженное нейронкой.
        """
        # Копируем исходный пост, чтобы не изменять оригинал
        post_copy = post.copy()
        # Извлекаем поле с изображением (оно может быть очень большим) и удаляем его из данных для нейронки
        image_data = post_copy.pop("image", None)
        # Получаем текст для анализа (например, по ключу "text")
        text = post_copy.get("text", "")
        if not text:
            logging.info("Пост не содержит текста – пропускаем обработку.")
            return []
        # Вызываем анализ текста; ожидаем, что вернется список событий (словарей)
        analysis_results = self.process(text)
        # Для каждого события добавляем данные изображения и остальные поля из исходного поста
        for event in analysis_results:
            if 'image' not in event or event.get('image') is None:
                event['image'] = image_data
            event.update(post_copy)
        return analysis_results
