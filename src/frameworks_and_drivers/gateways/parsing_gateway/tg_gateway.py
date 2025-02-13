import logging
from typing import List, Dict
from io import BytesIO
import re

from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

logging.basicConfig(level=logging.INFO)


class TelegramGateway(BaseGateway):
    def __init__(self, client=None) -> None:
        """
        Инициализирует объект TelegramGateway:
         - Считывает конфигурацию из config_file.
         - Загружает список каналов из channels_file.
         - Создает и подключает клиента Telethon.
         - Если клиент не авторизован, выбрасывает исключение (автоматизированный запуск не предполагает интерактивной авторизации).
         - Загружает состояние (последний обработанный message_id) из state_file.
        """

        self.API_ID = 29534008
        self.API_HASH = "7e0ecc08aefbd1039bc9929197e051d5"
        self.SESSION_NAME = "tg_max_parser_1514_session"

        self.channels = ["@checkapinow", "@Events_nn_best"]

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

            for msg in messages:
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
                        if isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
                            if hasattr(entity, "url") and entity.url:
                                url = entity.url
                            else:
                                url = msg.message[
                                    entity.offset : entity.offset + entity.length
                                ]
                            links.append(url)
                else:
                    # Если сущностей нет, пытаемся найти ссылки через регулярное выражение
                    found_links = re.findall(r"(https?://\S+)", msg.message)
                    for url in found_links:
                        links.append(url)
                print("Ссылки: ", links)
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
        return events
