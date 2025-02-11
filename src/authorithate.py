# authorize.py
from telethon.sync import TelegramClient
from telethon.errors import SessionPasswordNeededError, AuthRestartError
import json

API_ID = 29534008
API_HASH = "7e0ecc08aefbd1039bc9929197e051d5"
SESSION_NAME = "tg_max_parser_1514_session"

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
client.connect()

if not client.is_user_authorized():
    phone = input("Введите номер телефона (в формате +123456789): ")
    try:
        client.send_code_request(phone)
        code = input("Введите код из Telegram: ")
        client.sign_in(phone, code)
    except SessionPasswordNeededError:
        password = input("Введите 2FA пароль: ")
        client.sign_in(password=password)
    except AuthRestartError:
        print("Ошибка авторизации, попробуйте снова.")

print("Авторизация прошла успешно. Сессия сохранена.")
client.disconnect()
