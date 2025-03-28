import logging
from io import BytesIO
from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from telethon.sessions import StringSession

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

import easyocr  # <-- Добавлено
from PIL import Image  # <-- Добавлено

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

        # Каналы оставляем как есть
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
            ("@Events_nn_best", "nn"),
            ("@nnevents_best", "nn"),
            ("@naukann", "nn"),
        ]
        # Инициализируем клиент Телеграм
        self.client = TelegramClient(
            StringSession(string), 29534008, "7e0ecc08aefbd1039bc9929197e051d5"
        )
        self._run_auth()

        # Инициализируем OCR
        self.ocr_reader = easyocr.Reader(["ru", "en"], gpu=False)

    def _run_auth(self) -> None:
        self.client.connect()
        if not self.client.is_user_authorized():
            raise Exception("TelegramClient не авторизован!")

    def get_sources(self):
        return self.channels

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
                    # Игнорируем служебные t.me-ссылки
                    if "https://t.me" in url:
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

    def _extract_text_from_image(self, image_bytes: bytes) -> str:
        """
        Извлекает текст с помощью easyocr и возвращает его
        с префиксом ocr_prefix'.
        """
        ocr_prefix = (
            "[Далее будет указан текст с изображения прикреплённого к посту, если на нём есть какая-то "
            "дополнительная информация - адрес, телефон, цена или что-то ещё ценное, чего нет в тексте, то "
            "добавь это в json. Если информация дублируется по разному, то в приоритете данные из "
            "текста поста.]"
        )
        if not image_bytes:
            return ""

        try:
            pil_image = Image.open(BytesIO(image_bytes))
            result = self.ocr_reader.readtext(pil_image)

            if not result:
                return ""

            recognized_text = "\n".join(
                [item[1].strip() for item in result if item[1].strip()]
            )
            if not recognized_text:
                return ""
            return f"\n{ocr_prefix}\n{recognized_text}"
        except Exception as e:
            logging.error(f"Ошибка OCR: {e}", exc_info=True)
            return ""

    def fetch_content(self, channel: str, city: str) -> list[dict]:
        """
        Получает сообщения из указанных каналов, добавляет
        к сообщению ссылку и текст, распознанный из картинки.
        """
        events = []
        logging.info(f"processing {channel}")
        messages = self.client.get_messages(channel, limit=10)
        logging.info("messages have been received.")

        for msg in messages:
            if msg.message:
                try:
                    image_bytes = self.get_image_bytes(msg)
                    links = self.get_links(msg)
                    logging.info("links has been got.")
                    pic_text = self._extract_text_from_image(image_bytes)
                    combined_text = msg.message

                    if links:
                        combined_text += "\n" + "\n".join(links)

                    if pic_text:
                        combined_text += pic_text

                    events.append(
                        {
                            "event_id": str(msg.id),
                            "channel": channel,
                            "text": combined_text,
                            "links": links,
                            "date": msg.date.isoformat() if msg.date else None,
                            "city": city,
                            "image": image_bytes,
                        }
                    )
                    logging.info("events has been processed.")
                except Exception as e:
                    logging.error(f"error while processing message from tg: {e}")

        return events
