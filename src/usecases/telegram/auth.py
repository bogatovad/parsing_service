from telethon.sync import TelegramClient
from telethon.sessions import StringSession


with TelegramClient(
    StringSession(), 29534008, "7e0ecc08aefbd1039bc9929197e051d5"
) as client:
    print(client.session.save())
