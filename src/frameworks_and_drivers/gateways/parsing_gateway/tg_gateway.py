import logging
from io import BytesIO

from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway
from telethon.sessions import StringSession


logging.basicConfig(level=logging.INFO)
logging.getLogger("telethon").setLevel(logging.WARNING)


class TelegramGateway(BaseGateway):
    def __init__(self, client=None) -> None:
        string = (
            "1ApWapzMBuyigOu4V36X4ov2onH-cJvmwdFTIMIiS7UAHaLVXYiVgx6X-CcGrSEIfFWjxuy7EcFvBWhPx-GVf-"
            "RbnlrXnh3-pKIl8hbt0uAIA4HVeVQcvaOfD1DgxmAQ1-xUWifiN9tqKwKH0CNzeIspvyNpd8KFE1CtSwY4PWK9KD4NJjr"
            "FeqdeNspIt0duhjs_CUD3PaQU3cQxTZGbWwWhtkZ_zAtHiLqpGyOfik3Cx8bmNefafMGuzhqAVk18uWu4u7wl3WEnLo9kCLH9e"
            "MuMEVgeDnUhfOpFKfplamZ509-awPQN7Ad0T7SvWMZ7wblXlOpNUqy1g8KS04lTl2he9ri_Ma0c="
        )
        self.channels = [("@Events_nn_best", "nn")]
        self.client = TelegramClient(
            StringSession(string), 29534008, "7e0ecc08aefbd1039bc9929197e051d5"
        )
        self._run_auth()

    def _run_auth(self) -> None:
        self.client.connect()
        if not self.client.is_user_authorized():
            raise Exception("TelegramClient не авторизован!")

    @staticmethod
    def get_links(msg) -> list[str]:
        links = []
        if msg.entities:
            for entity in msg.entities:
                if isinstance(entity, (MessageEntityUrl, MessageEntityTextUrl)):
                    url = (
                        entity.url
                        if hasattr(entity, "url") and entity.url
                        else msg.message[entity.offset : entity.offset + entity.length]
                    )
                    if url.find("https://t.me") != -1:
                        continue
                    links.append(url)
        return links

    def get_image_bytes(self, msg) -> bytes:
        image_bytes = None
        if msg.media:
            try:
                file_obj = BytesIO()
                self.client.download_media(msg.media, file=file_obj)
                image_bytes = file_obj.getvalue()
                logging.info("image has been downloaded.")
            except Exception as e:
                logging.error(f"Ошибка скачивания медиа: {e}", exc_info=True)
        return image_bytes

    def fetch_content(self) -> list[dict]:
        """
        Получает сообщения из указанных каналов.
        """
        events = []
        for channel, city in self.channels:
            logging.info(f"processing {channel}")
            messages = self.client.get_messages(channel, limit=50)
            logging.info("messages have been received.")
            for msg in messages:
                if msg.message:
                    image_bytes = self.get_image_bytes(msg)  # noqa: F841
                    links = self.get_links(msg)
                    logging.info("links has been got.")
                    events.append(
                        {
                            "event_id": str(msg.id),
                            "channel": channel,
                            "text": msg.message + "\n".join(links),
                            "links": links,
                            "date": msg.date.isoformat() if msg.date else None,
                            "city": city,
                            "image": image_bytes,
                        }
                    )
                    logging.info("events has been processed.")
        return events
