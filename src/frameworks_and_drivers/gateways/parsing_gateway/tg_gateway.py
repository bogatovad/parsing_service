import logging
from typing import List, Dict
from io import BytesIO
import re

from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

logging.basicConfig(level=logging.INFO)
logging.getLogger("telethon").setLevel(logging.WARNING)


class TelegramGateway(BaseGateway):
    def __init__(self, client=None) -> None:
        self.API_ID = 29534008
        self.API_HASH = "7e0ecc08aefbd1039bc9929197e051d5"
        self.SESSION_NAME = "tg_max_parser_1514_session"

        self.channels = ["@checkapinow"]
        self.client = TelegramClient(self.SESSION_NAME, self.API_ID, self.API_HASH)
        self.client.connect()
        if not self.client.is_user_authorized():
            logging.error(
                "Клиент не авторизован. "
                "Запустите авторизацию вручную один раз, чтобы сохранить сессию, "
                "либо настройте автоматическую авторизацию через конфигурацию."
            )
            raise Exception("TelegramClient не авторизован!")

    def fetch_content(self) -> List[Dict]:
        """
        Получает новые сообщения из указанных каналов.
        """
        events = []
        for channel in self.channels:
            logging.info(f"processing {channel}")
            messages = self.client.get_messages(channel, limit=50)
            logging.info("messages have been received.")

            for msg in messages:
                image_bytes = None

                if msg.media:
                    try:
                        file_obj = BytesIO()
                        self.client.download_media(msg.media, file=file_obj)
                        image_bytes = file_obj.getvalue()
                        logging.info("image has been downloaded.")
                    except Exception as e:
                        logging.error(f"Ошибка скачивания медиа: {e}", exc_info=True)

                links = []
                if msg.entities:
                    links = [
                        msg.message[entity.offset : entity.offset + entity.length]
                        for entity in msg.entities
                        if isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl))
                    ]
                else:
                    links = re.findall(r"https?://\S+", msg.message or "")

                logging.info("links has been got.")
                full_text = (
                    f"{msg.message}\n" + "\n".join(links) if links else msg.message
                )

                events.append(
                    {
                        "event_id": msg.id,
                        "channel": channel,
                        "text": full_text,
                        "date": msg.date.isoformat() if msg.date else None,
                        "image": image_bytes,
                    }
                )
                logging.info("events has been processed.")
        return events
