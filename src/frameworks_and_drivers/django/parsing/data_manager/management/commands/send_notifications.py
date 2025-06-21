import logging
import os
import sys
import requests
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from pyrogram import Client
from pyrogram.raw.functions.contacts import ResolveUsername
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


# Настройки для Telegram
class TelegramSettings(BaseSettings):
    BOT_TOKEN: str = "7517129777:AAHtVmXMsaa130ebt5HyPFgkWoYRWJgfZt4"
    API_ID: str = "18640708"
    API_HASH: str = "202b12968ca21dbf7c7049bb657f81d1"
    model_config = SettingsConfigDict()


class Command(BaseCommand):
    help = "Send event notifications to users about their favorite events today"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what notifications would be sent without actually sending them",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        try:
            settings = TelegramSettings()
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Ошибка загрузки настроек Telegram: {e}")
            )
            return

        try:
            self.stdout.write("📱 Starting event notifications task")

            # Создаем клиент Pyrogram
            pyrogram_client = Client(
                "notification_bot",
                api_id=settings.API_ID,
                api_hash=settings.API_HASH,
                bot_token=settings.BOT_TOKEN,
                app_version="7.7.2",
                device_model="Lenovo Z6 Lite",
                system_version="11 R",
            )

            def resolve_username_to_user_id(username: str) -> int | None:
                if dry_run:
                    self.stdout.write(f"🔍 DRY RUN: Would resolve username {username}")
                    return 12345  # Mock ID for dry run

                with pyrogram_client:
                    try:
                        r = pyrogram_client.invoke(ResolveUsername(username=username))
                        if r.users:
                            return r.users[0].id
                        return None
                    except Exception as e:
                        logger.warning(f"Ошибка получения ID для {username}: {e}")
                        return None

            def send_telegram_message(chat_id: int, message: str) -> bool:
                if dry_run:
                    self.stdout.write(f"🔍 DRY RUN: Would send message to {chat_id}:")
                    self.stdout.write(f"Message: {message[:100]}...")
                    return True

                """Отправка сообщения через Telegram HTTP API"""
                try:
                    url = (
                        f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
                    )
                    payload = {
                        "chat_id": chat_id,
                        "text": message,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": False,
                    }
                    response = requests.post(url, json=payload)
                    return response.status_code == 200
                except Exception as e:
                    logger.error(f"Ошибка отправки сообщения: {e}")
                    return False

            def format_event_dates(event) -> str:
                """Форматирование дат события"""
                if not event.date_end or event.date_start == event.date_end:
                    return f"📅 {event.date_start.strftime('%d.%m.%Y')}"
                return f"📅 {event.date_start.strftime('%d.%m.%Y')} - {event.date_end.strftime('%d.%m.%Y')}"

            # Получаем сегодняшнюю дату
            today = timezone.now().date()
            self.stdout.write(f"📅 Поиск событий на {today}")

            # Импортируем модели основного проекта
            try:
                # Добавляем путь к основному проекту если нужно
                main_project_path = "/app"  # Путь к основному проекту в контейнере
                if main_project_path not in sys.path:
                    sys.path.append(main_project_path)

                # Настраиваем Django для основного проекта
                os.environ.setdefault("DJANGO_SETTINGS_MODULE", "event_afisha.settings")
                os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

                import django

                django.setup()

                from frameworks_and_drivers.django.parsing.data_manager.models import (
                    Like,
                )

            except ImportError as e:
                self.stdout.write(
                    self.style.ERROR(
                        f"❌ Ошибка импорта моделей основного проекта: {e}"
                    )
                )
                return

            # Получаем лайки на события сегодня
            today_likes = Like.objects.select_related("user", "content").filter(
                Q(
                    # Однодневные события или события без даты окончания
                    Q(content__date_end__isnull=True) & Q(content__date_start=today)
                )
                | Q(
                    # Многодневные события
                    Q(content__date_start__lte=today) & Q(content__date_end__gte=today)
                ),
                value=True,  # Только положительные лайки (избранное)
            )

            self.stdout.write(
                f"❤️ Найдено {today_likes.count()} избранных событий на сегодня"
            )

            # Группируем события по пользователям
            user_events = {}
            for like in today_likes:
                if like.user not in user_events:
                    user_events[like.user] = []
                user_events[like.user].append(like.content)

            self.stdout.write(
                f"👥 Пользователей с избранными событиями: {len(user_events)}"
            )

            if dry_run:
                self.stdout.write(self.style.WARNING("🔍 DRY RUN MODE"))
                for user, events in user_events.items():
                    self.stdout.write(
                        f"  User: {user.username} - Events: {len(events)}"
                    )
                    for event in events[:2]:  # Показываем первые 2 события
                        self.stdout.write(f"    - {event.name[:50]}...")
                return

            # Отправляем уведомления каждому пользователю
            sent_count = 0
            error_count = 0

            for user, events in user_events.items():
                try:
                    # Получаем Telegram ID пользователя
                    telegram_id = resolve_username_to_user_id(user.username)
                    if not telegram_id:
                        self.stdout.write(
                            self.style.WARNING(
                                f"⚠️ Не удалось получить Telegram ID для {user.username}"
                            )
                        )
                        error_count += 1
                        continue

                    # Формируем текст сообщения
                    message = (
                        "🎉 Привет! У вас сегодня актуальны следующие мероприятия:\n\n"
                    )

                    for event in events:
                        message += f"<b>{event.name}</b>\n"
                        message += f"{format_event_dates(event)}\n"

                        if event.time:
                            message += f"⏰ Время: {event.time}\n"
                        if event.location:
                            message += f"📍 Место: {event.location}\n"

                        # Добавляем ссылку на событие
                        event_link = (
                            f"https://t.me/EventAfishaBot/strelka?startapp={event.id}"
                        )
                        message += (
                            f"🔗 <a href='{event_link}'>Открыть в приложении</a>\n\n"
                        )

                    # Отправляем сообщение
                    if send_telegram_message(telegram_id, message):
                        self.stdout.write(
                            f"✅ Уведомление отправлено пользователю {user.username}"
                        )
                        sent_count += 1
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f"❌ Не удалось отправить уведомление пользователю {user.username}"
                            )
                        )
                        error_count += 1

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"❌ Ошибка обработки пользователя {user.username}: {e}"
                        )
                    )
                    error_count += 1
                    continue

            # Итоговый отчет
            self.stdout.write("\n📊 Отчет об отправке уведомлений:")
            self.stdout.write(f"  ✅ Успешно отправлено: {sent_count}")
            self.stdout.write(f"  ❌ Ошибки: {error_count}")
            self.stdout.write(f"  👥 Всего пользователей: {len(user_events)}")
            self.stdout.write(
                f"  🎭 Всего событий: {sum(len(events) for events in user_events.values())}"
            )

            if error_count == 0:
                self.stdout.write(
                    self.style.SUCCESS("🎉 Все уведомления отправлены успешно!")
                )
            elif sent_count > 0:
                self.stdout.write(
                    self.style.WARNING("⚠️ Уведомления отправлены с некоторыми ошибками")
                )
            else:
                self.stdout.write(
                    self.style.ERROR("❌ Не удалось отправить ни одного уведомления")
                )

            logger.info(
                f"Notifications task completed: {sent_count} sent, {error_count} errors"
            )

        except Exception as e:
            error_msg = f"❌ Ошибка в задаче уведомлений: {e}"
            self.stdout.write(self.style.ERROR(error_msg))
            logger.error(error_msg, exc_info=True)
            raise
