# tg_gateway.py
import json
import os
import logging
from typing import List, Dict
from io import BytesIO
import requests
import re

from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

logging.basicConfig(level=logging.INFO)


def expand_url(url: str) -> str:
    """
    Пытается выполнить HEAD-запрос к ссылке с перенаправлением,
    чтобы получить финальный URL (если ссылка сокращена или происходит редирект).
    Если не удалось, возвращает исходный URL.
    """
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    except Exception as e:
        logging.error(f"Ошибка при раскрытии ссылки {url}: {e}")
        return url


def load_config(config_file: str = "telegram_config.json") -> dict:
    """
    Загружает конфигурацию Telegram из указанного JSON-файла.
    """
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Файл конфигурации '{config_file}' не найден.")


def load_channels(filename: str = "channels.txt") -> List[str]:
    """
    Загружает список каналов из указанного текстового файла.
    Каждый канал должен быть указан на отдельной строке.
    """
    channels = []
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                channel = line.strip()
                if channel:
                    channels.append(channel)
    else:
        logging.warning(f"Файл '{filename}' не найден.")
    return channels


class TelegramGateway(BaseGateway):
    def __init__(
        self,
        state_file: str = "last_processed.json",
        config_file: str = "telegram_config.json",
        channels_file: str = "channels.txt",
    ) -> None:
        """
        Инициализирует объект TelegramGateway:
         - Считывает конфигурацию из config_file.
         - Загружает список каналов из channels_file.
         - Создает и подключает клиента Telethon.
         - Если клиент не авторизован, выбрасывает исключение (автоматизированный запуск не предполагает интерактивной авторизации).
         - Загружает состояние (последний обработанный message_id) из state_file.
        """
        # Загружаем конфигурацию
        config = load_config(config_file)
        self.API_ID = config.get("API_ID")
        self.API_HASH = config.get("API_HASH")
        self.SESSION_NAME = config.get("SESSION_NAME")

        # Загружаем список каналов
        self.channels = load_channels(channels_file)
        self.state_file = state_file

        # Создаем клиента Telethon и подключаемся
        self.client = TelegramClient(self.SESSION_NAME, self.API_ID, self.API_HASH)
        self.client.connect()

        # Если клиент не авторизован, выбрасываем исключение.
        if not self.client.is_user_authorized():
            logging.error(
                "Клиент не авторизован. "
                "Запустите авторизацию вручную один раз, чтобы сохранить сессию, либо настройте автоматическую авторизацию через конфигурацию."
            )
            raise Exception("TelegramClient не авторизован!")

        # Загружаем состояние (последний обработанный message_id для каждого канала)
        self.last_processed = self._load_state()

    def _load_state(self) -> Dict[str, int]:
        """
        Загружает состояние из файла state_file.
        Если файл отсутствует или происходит ошибка, инициализирует состояние значением 0 для каждого канала.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Ошибка загрузки состояния: {e}")
        return {channel: 0 for channel in self.channels}

    def _save_state(self) -> None:
        """
        Сохраняет текущее состояние (последний обработанный message_id для каждого канала) в файл state_file.
        """
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.last_processed, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Ошибка сохранения состояния: {e}")

    def fetch_content(self) -> List[Dict]:
        """
        Получает новые сообщения из указанных каналов.
        Для каждого сообщения собирает:
            - "event_id": уникальный идентификатор сообщения,
            - "channel": имя канала,
            - "text": текст сообщения вместе с раскрытыми ссылками,
            - "date": дата публикации (в ISO формате),
            - "image": содержимое медиа в виде байтов (если есть).

        Возвращает список словарей с данными сообщений.
        """
        events = []
        for channel in self.channels:
            # Получаем последние 50 сообщений для канала
            messages = self.client.get_messages(channel, limit=50)
            new_messages = []
            last_id = self.last_processed.get(channel, 0)
            for msg in messages:
                if msg.id > last_id:
                    new_messages.append(msg)
            if new_messages:
                # Обновляем состояние: сохраняем максимальный message_id для канала
                max_id = max(msg.id for msg in new_messages)
                self.last_processed[channel] = max_id
                for msg in new_messages:
                    image_bytes = None
                    # Если сообщение содержит медиа, пытаемся скачать его в байтовом формате
                    if msg.media:
                        try:
                            file_obj = BytesIO()
                            self.client.download_media(msg.media, file=file_obj)
                            file_obj.seek(0)
                            image_bytes = file_obj.read()
                        except Exception as e:
                            logging.error(f"Ошибка скачивания медиа: {e}")

                    # Извлекаем ссылки из сообщения
                    links = []
                    if msg.entities:
                        for entity in msg.entities:
                            if isinstance(
                                entity, (MessageEntityUrl, MessageEntityTextUrl)
                            ):
                                if hasattr(entity, "url") and entity.url:
                                    url = entity.url
                                else:
                                    url = msg.message[
                                        entity.offset : entity.offset + entity.length
                                    ]
                                links.append(expand_url(url))
                    else:
                        # Если сущностей нет, пытаемся найти ссылки через регулярное выражение
                        found_links = re.findall(r"(https?://\S+)", msg.message)
                        for url in found_links:
                            links.append(expand_url(url))

                    # Вместо того, чтобы возвращать ссылки отдельно, добавляем их в текст сообщения
                    full_text = msg.message
                    if links:
                        full_text += "\n" + "\n".join(links)

                    events.append(
                        {
                            "event_id": msg.id,
                            "channel": channel,
                            "text": full_text,  # Передаём объединённый текст с ссылками
                            "date": msg.date.isoformat() if msg.date else None,
                            "image": image_bytes,
                        }
                    )
        self._save_state()
        return events


if __name__ == "__main__":
    try:
        gateway = TelegramGateway()
        events = gateway.fetch_content()
        if events:
            print("Полученные новые сообщения:")
            for event in events:
                print(event)
        else:
            print("Новых сообщений не найдено.")
    except Exception as e:
        logging.error(f"Ошибка в работе TelegramGateway: {e}")
