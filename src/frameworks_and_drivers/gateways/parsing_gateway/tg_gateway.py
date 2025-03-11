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
            "1ApWapzMBu2BNT4SectEoG19zFpAL64hVdg9UNVgDoWYlX9kcpBqB3wy87A-_gQT"
            "u5ZB1RWzyft7fBQI9S0tNryjIcpNGH7dnyU13fQN0gAwft_3gePRrh5oF2XgnMk_bN3"
            "3bwI15TAMUSbmZQUlzwYmmS-NIDhH-YzTJ5YHY_UjYu3v7ME9UZ-oiFnvXzTL6_lN_KVeMw78"
            "cqNguzy2W9JUHsw_zSu1qgHJwlT9a4IsIRgBOpK53eWOzMjZP0zuq39U4MGHoulGcGN-wKgYUhKP8zeD5Glxq_g"
            "yWv0tvBq6COknZRtSSAacLhN5w9Re5NfQ53OCNDyIlBpdYhP9vmZIdRK-b2A8="
        )
        self.channels = [
            ("@opera_nn", "nn"),
            ("@moynizhny", "nn"),
            ("@molodezh_no", "nn"),
            ("@planetarium_nn", "nn"),
            ("@nizhny800", "nn"),
            ("@mynnovgorod", "nn"),
            ("@rmfmuseum", "nn"),
            ("@af_nn800", "nn"),
            ("@nn_basket", "nn"),
            ("@gorkoNN", "nn"),
            ("@fudgid", "nn"),
            ("@nizhny801", "nn"),
            ("@runc_run", "nn"),
            ("@domarchin", "nn"),
            ("@NNafisha", "nn"),
            ("@rupor_nnov", "nn"),
            # ("@kupnonn", "nn"),
            ("@Events_nn_best", "nn"),
            ("@nnevents_best", "nn"),
            # ("@silenceworkshop", "nn"),
            # ("@ninogda", "nn"),
            # ("@dvig_nn_afisha", "nn"),
            # ("@standupClub52", "nn"),
            # ("@zaotdih_nn", "nn"),
            # ("@mininuniver", "nn"),
            # ("@villagenn", "nn"),
            # ("@mishakudago", "nn"),
            # ("@runheroNN", "nn"),
            # ("@nnmuseum", "nn"),
            # ("@pushkinmuseum_volga", "nn"),
            # ("@nn_yarmarka", "nn"),
            # ("@kassirrunn", "nn"),
            # ("@matveeva_juli", "nn"),
            # ("@nn_philharmonic", "nn"),
            # ("@pivzavod_nn", "nn"),
            # ("@it52info", "nn"),
            # ("@dk_gaz", "nn"),
            # ("@ano_asiris", "nn"),
            # ("@recordcult", "nn"),
            # ("@terminal_nn", "nn"),
            # ("@arsenalmolod", "nn"),
            ("@naukann", "nn"),
            # ("@shtab_kvartira_nn", "nn"),
        ]
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
            messages = self.client.get_messages(channel, limit=10)
            logging.info("messages have been received.")
            for msg in messages:
                if msg.message:
                    try:
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
                    except:  # noqa: E722
                        logging.info("error while processing message from tg.")
        return events
