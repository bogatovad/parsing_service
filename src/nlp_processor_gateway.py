# nlp_processor_gateway.py
import json
import re
import time
import requests
import yaml
import logging
import os

from interface_adapters.gateways.npl_base_gateway.base_nlp_processor import NLPProcessorBase

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

class NLPProcessor(NLPProcessorBase):
    def __init__(self, config_file: str = "nlp_config.json", prompt_file: str = "nlp_prompts.yaml") -> None:
        """
        Инициализирует NLPProcessor.
        Загружает конфигурацию (ключи API, число попыток, интервалы) из JSON-файла,
        а также промпты из YAML-файла.
        """
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        self.thebai_api_url = config.get("THEBAI_API_URL", "https://api.theb.ai/v1/chat/completions")
        self.thebai_api_key = config.get("THEBAI_API_KEY", "sk-te5U1TN6yvTYFuB8Nc8FVGhlQi5BSQL7dkdAaPePqRXNf7Wu")
        self.openrouter_api_url = config.get("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
        self.openrouter_api_key = config.get("OPENROUTER_API_KEY", "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")
        self.attempts = config.get("attempts", 3)
        self.attempt_interval = config.get("attempt_interval", 60)  # в секундах

        with open(prompt_file, "r", encoding="utf-8") as f:
            self.prompt_config = yaml.safe_load(f)

    def _parse_response(self, response_text: str) -> dict:
        """
        Унифицированная обработка ответа.
        Если ответ равен "[НЕ АФИША]", возвращается пустой словарь.
        Далее пытается разделить ответ по тегу [РАЗДЕЛЕНИЕ] и распарсить JSON.
        Если парсинг не удаётся, сохраняет ответ в файл unparsed_response.txt и возвращает {}.
        """
        # Если ответ равен "[НЕ АФИША]"
        if response_text.strip() == "[НЕ АФИША]":
            return {}

        # Убираем лишние обратные кавычки
        response_text = re.sub(r"```", "", response_text).strip()

        try:
            # Если ответ начинается с [ и заканчивается ], попробуем убрать разделители
            if response_text.startswith("[") and response_text.endswith("]"):
                response_clean = re.sub(r'\[РАЗДЕЛЕНИЕ\]\s*,?\s*', '', response_text)
                parsed = json.loads(response_clean)
                if isinstance(parsed, list):
                    # Вернуть первый словарь, если список не пуст
                    return parsed[0] if parsed and isinstance(parsed[0], dict) else {}
                elif isinstance(parsed, dict):
                    return parsed
                else:
                    return {}
            else:
                # Иначе, пробуем разделить по тегу [РАЗДЕЛЕНИЕ]
                blocks = re.split(r'\[РАЗДЕЛЕНИЕ\]\s*,?\s*', response_text)
                results = []
                for block in blocks:
                    block = block.strip()
                    if block:
                        results.append(json.loads(block))
                if results:
                    return results[0] if isinstance(results[0], dict) else {}
                return {}
        except Exception as e:
            logging.error(f"Ошибка парсинга ответа: {e}")
            # Сохраняем ответ в файл для анализа
            try:
                with open("unparsed_response.txt", "a", encoding="utf-8") as f:
                    f.write(response_text + "\n\n")
            except Exception as file_e:
                logging.error(f"Ошибка сохранения в unparsed_response.txt: {file_e}")
            return {}

    def _call_api(self, prompt: str, service: str = "thebai") -> dict:
        """
        Унифицированный метод для вызова внешнего API с несколькими попытками.
        Если service == "thebai", обращается к основному сервису, иначе – к openrouter.
        При неудаче при вызове основного сервиса переключается на openrouter.
        Возвращает результат, обработанный функцией _parse_response.
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

        # Если не удалось получить ответ с текущим сервисом и это основной сервис, переключаемся на openrouter
        if service == "thebai":
            logging.info("Переключение на сервис OpenRouter.")
            return self._call_api(prompt, service="openrouter")
        return {}

    def process(self, text: str) -> dict:
        """
        Основной метод обработки текста.
        Использует промпт main_prompt из YAML, подставляет в него текст и вызывает _call_api.
        """
        main_prompt_template = self.prompt_config.get("main_prompt", "")
        prompt = main_prompt_template.format(text=text)
        return self._call_api(prompt, service="thebai")

    def determine_category(self, event_text: str) -> str:
        """
        Определяет категорию мероприятия.
        Использует шаблон category_prompt из YAML.
        Возвращает строку с категорией.
        """
        category_prompt_template = self.prompt_config.get("category_prompt", "Определи категорию: {text}")
        prompt = category_prompt_template.format(text=event_text)
        result = self._call_api(prompt, service="thebai")
        # Если result пустой, можно вернуть пустую строку
        if isinstance(result, dict) and result:
            # Предполагаем, что ответ – текст
            return str(result.get("category", "")).strip() or str(result).strip()
        return ""

    def generate_link_title(self, event_text: str) -> str:
        """
        Генерирует название для ссылки.
        Использует шаблон link_title_prompt из YAML.
        Возвращает сгенерированное название.
        """
        link_prompt_template = self.prompt_config.get("link_title_prompt", "Придумай название для ссылки: {text}")
        prompt = link_prompt_template.format(text=event_text)
        result = self._call_api(prompt, service="thebai")
        if isinstance(result, dict) and result:
            return str(result.get("link_title", "")).strip() or str(result).strip()
        return ""
