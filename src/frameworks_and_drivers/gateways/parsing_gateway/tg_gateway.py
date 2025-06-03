import logging
from io import BytesIO
from telethon.sync import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl
from telethon.sessions import StringSession

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway

# import easyocr
# from PIL import Image
# import re

logging.basicConfig(level=logging.DEBUG)
logging.getLogger("telethon").setLevel(logging.WARNING)


class TelegramGateway(BaseGateway):
    def __init__(self) -> None:
        """
        Класс, отвечающий за получение сообщений из Telegram-каналов,
        вычитывание OCR с изображений и подготовку сырых постов для дальнейшей обработки.
        """
        # Session-строка для авторизации клиента
        string = (
            "1ApWapzMBuxm4BydlDfdR1q_uprG8d8Okvgj-uL9QVLOigYPgDvITZLjCuq-VEVamdHsqlCPOGQ8dAv3m4Ax-Mu6ARVOaeCKK9e6H"
            "7xj06Eud7KH_keGun4_gbKCnlTJp4Us2HnFdCW31Rrt40NC95-DRPOdZkWHKZ4czSw6NmEm7L_RC-f84DafHqpMJUkYIs8v0SJVTRH"
            "i5N3f56bjCAokiPG7BRYuUILCwnnXuHB4VFJmA-z9MNLm4mkCZOhOZx6rwiD6HTWTWjcsM5uOUtqpDdVjR-LZ_1XVkFvYOqpT7T5Dix"
            "TfLF6xlbpsq2tJE3vELUyvxKBXbsR4lM8wihAcnoqrRT0Q="
        )

        # Список каналов. По структуре: [(имя_канала, город), ...]
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

        self.client = TelegramClient(
            StringSession(string),
            29534008,  # ваш api_id
            "7e0ecc08aefbd1039bc9929197e051d5",  # ваш api_hash
        )
        self._run_auth()

        # EasyOCR для распознавания текста на картинках
        # self.ocr_reader = easyocr.Reader(["ru", "en"], gpu=False)

    def _run_auth(self) -> None:
        self.client.connect()
        if not self.client.is_user_authorized():
            raise Exception("TelegramClient не авторизован!")
        logging.debug("TelegramClient авторизован.")

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
                    # Игнорируем служебные ссылки t.me
                    if "https://t.me" in url:
                        continue
                    links.append(url)
        return links

    def is_image_message(self, msg) -> bool:
        """
        Проверяем, является ли вложение сообщением с изображением.
        """
        if msg.photo:
            return True
        if msg.document and getattr(msg.document, "mime_type", None):
            return msg.document.mime_type.startswith("image/")
        return False

    def get_image_bytes(self, msg) -> bytes:
        """
        Скачиваем байты изображения из сообщения, если оно изображение.
        """
        image_bytes = b""
        try:
            file_obj = BytesIO()
            self.client.download_media(msg.media, file=file_obj)
            image_bytes = file_obj.getvalue()
            logging.debug(
                "Изображение скачано успешно, размер (байт): %s", len(image_bytes)
            )
        except Exception as e:
            logging.error(f"Ошибка скачивания медиа: {e}", exc_info=True)
        return image_bytes

    # def _extract_text_from_image(self, image_bytes: bytes) -> str:
    #     """
    #     Извлекает текст с помощью easyocr и возвращает его
    #     с префиксом, если распознанный текст не пуст.
    #     """
    #     if not image_bytes:
    #         logging.debug("Пустые байты для OCR, пропускаем.")
    #         return ""
    #
    #     ocr_prefix = (
    #         "Далее будет указан текст с изображения прикреплённого к посту, "
    #         "если на нём есть какая-то дополнительная информация (адрес, телефон, цена и т.д.), "
    #         "добавь это в json. Если информация дублируется по разному, "
    #         "то в приоритете данные из текста поста. Текст с картинки:"
    #     )
    #     try:
    #         pil_image = Image.open(BytesIO(image_bytes))
    #         result = self.ocr_reader.readtext(pil_image)
    #
    #         if not result:
    #             logging.debug("EasyOCR не распознала текст на изображении.")
    #             return ""
    #
    #         # Склеим все строки OCR в одну строку, убирая повторные пробелы/переносы
    #         recognized_text = " ".join(
    #             item[1].strip() for item in result if item[1].strip()
    #         )
    #         recognized_text = re.sub(r"\s+", " ", recognized_text).strip()
    #
    #         if not recognized_text:
    #             logging.debug("OCR вернула пустой текст после очистки.")
    #             return ""
    #
    #         logging.debug("OCR вернула текст:\n%s", recognized_text)
    #         return f"\n{ocr_prefix}\n{recognized_text}"
    #     except Exception as e:
    #         logging.error(f"Ошибка OCR (возможно, не изображение): {e}", exc_info=True)
    #         return ""

    def get_sources(self):
        return self.channels

    def fetch_content(self, channel: str, city: str) -> list[dict]:
        """
        Получает сообщения из Telegram-канала, вычленяет ссылки,
        распознаёт OCR, возвращает список словарей с полями:
          - event_id
          - channel
          - text
          - links
          - date
          - city
          - image (байты)
        """
        events = []
        logging.debug(f"Получаем сообщения из канала: {channel}, город: {city}")
        messages = self.client.get_messages(channel, limit=15)  # 15 сообщений, например
        logging.debug("Из канала %s получено сообщений: %s", channel, len(messages))

        for msg in messages:
            if not msg.message:
                logging.debug(f"Сообщение ID={msg.id} пустое, пропускаем.")
                continue

            try:
                logging.debug(f"=== Начало обработки сообщения ID={msg.id} ===")

                # Извлекаем ссылки
                links = self.get_links(msg)
                if links:
                    logging.debug("Извлечённые ссылки: %s", links)

                combined_text = msg.message
                logging.debug("Исходный текст сообщения:\n%s", combined_text)

                if links:
                    combined_text += "\n" + "\n".join(links)

                # Проверяем, есть ли изображение
                if self.is_image_message(msg):
                    logging.debug(
                        "Сообщение ID=%s содержит изображение. Скачиваем...", msg.id
                    )
                    image_bytes = self.get_image_bytes(msg)
                else:
                    image_bytes = b""

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

                logging.debug(f"Итоговый текст сообщения ID={msg.id}:\n{combined_text}")
                logging.debug(f"=== Конец обработки сообщения ID={msg.id} ===")
            except Exception as e:
                logging.error(
                    f"Ошибка при обработке сообщения ID={msg.id}: {e}", exc_info=True
                )

        return events
