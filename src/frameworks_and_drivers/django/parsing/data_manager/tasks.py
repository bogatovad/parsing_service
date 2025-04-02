import os
from datetime import datetime, timedelta
from celery import shared_task
from celery.utils.log import get_task_logger
from django.utils import timezone
from django.db.models import Prefetch
import requests
from pyrogram.errors import FloodWait
import time

#скорее всего две строчки ниже надо поправить, потому что это в parsing_service реализовано
#посмотреть как правильно
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from .models import User, Like

logger = get_task_logger(__name__)

users = ['337420370']
# там мой user_id стоит
TELEGRAM_BOT_TOKEN = "токен"
BOT_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"


@shared_task
def send_daily_notifications():

    today = timezone.now().date()

    users = User.objects.prefetch_related(
        Prefetch(
            'likes',
            queryset=Like.objects.filter(
                value=True,
                content__date_start__date=today  # События, начинающиеся сегодня
            ).select_related('content')
        )
    ).distinct()


    for user in users:

        relevant_likes = user.likes.all()

        if not relevant_likes:
            continue


        init_message = f"🎉 Привет!\nНе забывай, что у тебя сегодня запланировано мероприятие!\n🔗 "
        end_message = f"Пусть это будет отличное время и море впечатлений! Наслаждайся! 😊✨"

        message_lines = []

        init_message = init_message if len(relevant_likes) == 1 else init_message.replace('запланировано мероприятие', 'запланированы мероприятия')

        for like in relevant_likes:
            event = like.content
            link = f"https://t.me/EventAfishaBot/strelka?startapp={like.content.id}"
            message_lines.append(f"- [{event.name}]({link})")

        message_lines.append(end_message)
        message = f'{init_message}' + "\n".join(message_lines) + end_message

        try:
            response = requests.post(
                BOT_API_URL,
                json={
                    "chat_id": user.telegram_id,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            response.raise_for_status()
            logger.info(f"Уведомление отправлено пользователю {user.username}")

        except FloodWait as e:
            wait_time = e.value + 5
            logger.warning(f"FloodWait: ожидание {wait_time} секунд...")
            time.sleep(wait_time)

        except Exception as e:
            logger.error(f"Ошибка отправки: {str(e)}")

    logger.info("Рассылка завершена")