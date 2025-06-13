import json
import time
import base64
import requests
import logging

logging.basicConfig(level=logging.INFO)

STYLE_PREFIX = (
    "Ты рисуешь картинку для анонса данного мероприятия. "
    "Не добавляй в изображение текст или цифры. Будь красивым и стильным, "
    "придерживайся фотореализма. Используй мягкие, размытые градиенты с "
    "желтым, розовым и фиолетовым цветами."
)


class Text2ImageAPI:
    """
    Класс для работы с API FusionBrain (Kandinsky).
    """

    def __init__(self, url: str, api_key: str, secret_key: str):
        self.URL = url
        self.AUTH_HEADERS = {
            "X-Key": f"Key {api_key}",
            "X-Secret": f"Secret {secret_key}",
        }

    def get_model(self) -> str:
        response = requests.get(
            self.URL + "key/api/v1/models", headers=self.AUTH_HEADERS
        )
        data = response.json()
        if not data:
            raise Exception("Нет доступных моделей Kandinsky.")
        return data[0]["id"]

    def generate(
        self,
        prompt: str,
        model_id: str,
        images: int = 1,
        width: int = 512,
        height: int = 512,
    ) -> str:
        params = {
            "type": "GENERATE",
            "numImages": images,
            "width": width,
            "height": height,
            "generateParams": {"query": prompt},
        }
        data = {
            "model_id": (None, str(model_id)),
            "params": (None, json.dumps(params), "application/json"),
        }
        response = requests.post(
            self.URL + "key/api/v1/text2image/run",
            headers=self.AUTH_HEADERS,
            files=data,
        )
        if response.status_code != 201:
            raise Exception(
                f"Ошибка при запуске генерации: {response.status_code}, {response.text}"
            )
        return response.json()["uuid"]

    def check_generation(
        self, request_id: str, attempts: int = 20, delay: int = 5
    ) -> list:
        for i in range(attempts):
            response = requests.get(
                self.URL + f"key/api/v1/text2image/status/{request_id}",
                headers=self.AUTH_HEADERS,
            )
            data = response.json()

            if data["status"] == "DONE":
                return data["images"]  # список Base64-строк
            elif data["status"] == "FAIL":
                raise Exception(f"Генерация не удалась: {data}")
            logging.info(f"Статус: {data['status']} (попытка {i+1}/{attempts})")
            time.sleep(delay)
        raise TimeoutError("Генерация не завершилась вовремя.")


def generate_image_with_kandinsky(prompt: str) -> bytes:
    """
    Функция генерирует изображение через Kandinsky, используя текст prompt,
    добавляя стилистический префикс STYLE_PREFIX.
    Возвращает изображение в виде байтов.
    """
    full_prompt = f"{prompt} {STYLE_PREFIX}"
    logging.info(f"Генерация изображения с промптом: {full_prompt}")

    api = Text2ImageAPI(
        url="https://api-key.fusionbrain.ai/",
        api_key="00EEC949FF0ECF10C121C3418FB59032",
        secret_key="5CF7C92EF37D0E49237EE30E4E724171",
    )
    model_id = api.get_model()
    uuid_task = api.generate(full_prompt, model_id, images=1, width=512, height=512)
    images_base64 = api.check_generation(uuid_task, attempts=15, delay=5)
    if not images_base64:
        logging.warning("Kandinsky не вернул изображений.")
        return b""
    image_data = base64.b64decode(images_base64[0])
    return image_data


generate_image_with_kandinsky(
    "Всероссийский марафон классической музыки «Кантата.Россия» — это концерты по всей стране от Владивостока до Калининграда. В Нижнем Новгороде концерт пройдет в концертном Пакгаузе при участии оркестра La Voce Strumentale."
)
