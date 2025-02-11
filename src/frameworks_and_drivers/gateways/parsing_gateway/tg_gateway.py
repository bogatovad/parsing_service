# tg_gateway.py
import json
import os
from typing import List, Dict

from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthRestartError

from interface_adapters.gateways.parsing_base_gateway.base_gateway import BaseGateway


def load_config(config_file: str = "telegram_config.json") -> dict:
    """
    Загружает конфигурацию Telegram API из JSON-файла.
    """
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        raise FileNotFoundError(f"Файл конфигурации '{config_file}' не найден.")


def load_channels(filename: str = "channels.txt") -> List[str]:
    """
    Загружает список каналов из текстового файла.
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
        print(f"Файл '{filename}' не найден.")
    return channels


class TelegramGateway(BaseGateway):
    def __init__(self, state_file: str = "last_processed.json", config_file: str = "telegram_config.json",
                 channels_file: str = "channels.txt") -> None:
        """
        Инициализирует объект TelegramGateway:
          - Считывает конфигурацию из config_file.
          - Загружает список каналов из channels_file.
          - Производит авторизацию через Telethon.
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

        # Инициализируем клиента Telethon
        self.client = TelegramClient(self.SESSION_NAME, self.API_ID, self.API_HASH)
        self.client.connect()

        # Авторизация, если клиент не авторизован
        if not self.client.is_user_authorized():
            phone = input("Введите номер телефона (в формате +123456789): ")
            try:
                self.client.send_code_request(phone)
                code = input("Введите код из Telegram: ")
                self.client.sign_in(phone, code)
            except SessionPasswordNeededError:
                password = input("Введите 2FA пароль: ")
                self.client.sign_in(password=password)
            except AuthRestartError:
                print("Ошибка авторизации, попробуйте снова.")

        # Загружаем состояние (последний обработанный message_id для каждого канала)
        self.last_processed = self._load_state()

    def _load_state(self) -> Dict[str, int]:
        """
        Загружает состояние (последний обработанный message_id) из файла.
        Если файл отсутствует, инициализирует состояние значением 0 для каждого канала.
        """
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки состояния: {e}")
        return {channel: 0 for channel in self.channels}

    def _save_state(self) -> None:
        """
        Сохраняет обновлённое состояние в файл.
        """
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.last_processed, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка сохранения состояния: {e}")

    def fetch_content(self) -> List[Dict]:
        """
        Получает новые сообщения из указанных каналов.

        :return: Список словарей с данными сообщений, где каждый словарь содержит:
                 - "event_id": уникальный идентификатор сообщения,
                 - "channel": имя канала,
                 - "text": текст сообщения,
                 - "date": дата публикации (в ISO формате).
        """
        events = []
        for channel in self.channels:
            # Получаем последние 15 сообщений для данного канала
            messages = self.client.get_messages(channel, limit=15)
            new_messages = []
            last_id = self.last_processed.get(channel, 0)
            for msg in messages:
                if msg.id > last_id:
                    new_messages.append(msg)
            if new_messages:
                # Обновляем состояние: сохраняем максимальный message_id из новых сообщений
                max_id = max(msg.id for msg in new_messages)
                self.last_processed[channel] = max_id
                for msg in new_messages:
                    events.append({
                        "event_id": msg.id,
                        "channel": channel,
                        "text": msg.message,
                        "date": msg.date.isoformat() if msg.date else None
                    })
        self._save_state()
        return events


# Если запускаем скрипт напрямую, можно протестировать работу gateway:
if __name__ == "__main__":
    gateway = TelegramGateway()
    events = gateway.fetch_content()
    if events:
        print("Полученные новые сообщения:")
        for event in events:
            print(event)
    else:
        print("Новых сообщений не найдено.")
