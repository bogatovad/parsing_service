import logging
from celery import shared_task, chain
from django.utils import timezone
from django.db.models import F, Q
from interface_adapters.controlles.content_controller import (
    GetContentTimepadController,
    GetContentTgController,
    GetContentKudaGoController,
    GetContentVKController,
    PlacesController,
)
from interface_adapters.controlles.factory import UseCaseFactory
from frameworks_and_drivers.django.parsing.data_manager.models import Content
from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
import requests
from pyrogram import Client
from pyrogram.raw.functions.contacts import ResolveUsername
from pydantic_settings import BaseSettings, SettingsConfigDict
import sys
import os

logger = logging.getLogger(__name__)

# Создаем фабрику и контроллеры один раз при загрузке модуля
factory_usecase = UseCaseFactory()
controller_timepad = GetContentTimepadController(usecase_factory=factory_usecase)
controller_tg = GetContentTgController(usecase_factory=factory_usecase)
controller_kuda_go = GetContentKudaGoController(usecase_factory=factory_usecase)
controller_vk = GetContentVKController(usecase_factory=factory_usecase)
controller_place = PlacesController(usecase_factory=factory_usecase)


# Настройки для Telegram
class TelegramSettings(BaseSettings):
    BOT_TOKEN: str = "7517129777:AAHtVmXMsaa130ebt5HyPFgkWoYRWJgfZt4"
    API_ID: str = "18640708"
    API_HASH: str = "202b12968ca21dbf7c7049bb657f81d1"
    model_config = SettingsConfigDict()


try:
    settings = TelegramSettings()
except Exception as e:
    logger.error(f"Ошибка загрузки настроек Telegram: {e}")


@shared_task(name="parse_telegram")
def parse_telegram():
    """Запуск парсера Telegram"""
    try:
        controller_tg.get_content()
        logger.info("Telegram parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Telegram parser: {str(e)}")
        return False


@shared_task(name="parse_vk")
def parse_vk():
    """Запуск парсера VK"""
    try:
        controller_vk.get_content()
        logger.info("VK parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in VK parser: {str(e)}")
        return False


@shared_task(name="parse_timepad")
def parse_timepad():
    """Запуск парсера Timepad"""
    try:
        controller_timepad.get_content()
        logger.info("Timepad parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Timepad parser: {str(e)}")
        return False


@shared_task(name="parse_kudago")
def parse_kudago():
    """Запуск парсера KudaGo"""
    try:
        controller_kuda_go.get_content()
        logger.info("KudaGo parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in KudaGo parser: {str(e)}")
        return False


@shared_task(name="parse_places")
def parse_places():
    """Запуск парсера Places"""
    try:
        controller_place.get_content()
        logger.info("Places parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Places parser: {str(e)}")
        return False


@shared_task(name="run_all_parsers")
def run_all_parsers():
    """
    Последовательный запуск всех парсеров.
    Каждый следующий парсер запускается только после успешного завершения предыдущего.
    """
    logger.info("Starting sequential parser execution")

    # Создаем цепочку задач
    parser_chain = chain(
        parse_telegram.s(),
        parse_vk.s(),
        parse_timepad.s(),
        parse_kudago.s(),
    )

    # Запускаем цепочку
    result = parser_chain()
    return result


@shared_task(name="run_main_parsers")
def run_main_parsers():
    """
    Последовательный запуск основных парсеров в порядке:
    1. KudaGo
    2. Timepad
    3. Telegram
    4. VK
    """
    logger.info("Starting sequential execution of main parsers")

    # Создаем цепочку задач в нужном порядке
    parser_chain = chain(
        parse_kudago.s(), parse_timepad.s(), parse_telegram.s(), parse_vk.s()
    )

    # Запускаем цепочку
    result = parser_chain.apply_async()

    logger.info("Main parsers chain has been started")
    return result


@shared_task(name="run_main_parsers_simple")
def run_main_parsers_simple():
    """
    Простой последовательный запуск основных парсеров без chain
    """
    logger.info("Starting simple sequential execution of main parsers")

    results = []
    parsers = [
        ("KudaGo", parse_kudago),
        ("Timepad", parse_timepad),
        ("Telegram", parse_telegram),
        ("VK", parse_vk),
    ]

    for parser_name, parser_func in parsers:
        try:
            logger.info(f"Starting {parser_name} parser...")
            result = parser_func()
            results.append({parser_name: result})
            logger.info(f"{parser_name} parser completed with result: {result}")
        except Exception as e:
            logger.error(f"Error in {parser_name} parser: {str(e)}")
            results.append({parser_name: f"ERROR: {str(e)}"})

    logger.info("All main parsers completed")
    return results


@shared_task(
    bind=True, max_retries=3, name="delete_outdated_events", ignore_result=False
)
def delete_outdated_events(self=None):
    """Task to delete old events based on date conditions."""
    try:
        logger.info("Starting deletion of outdated events")
        logger.info(f"Task execution time: {timezone.now()}")

        # Используем текущую дату в UTC
        today = timezone.now().date()

        logger.info(
            f"Deleting events that ended before {today} (UTC). Today is {today}"
        )
        logger.info(f"Current timezone: {timezone.get_current_timezone()}")

        # 1. События с указанными датами начала и окончания (многодневные, которые уже завершились)
        multi_day_events = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & ~Q(date_start=F("date_end"))  # Исключаем однодневные события
            & Q(date_end__lt=today)  # Удаляем события, закончившиеся ДО сегодня
        )

        # 2. Однодневные события без даты окончания
        single_day_no_end = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=True)
            & Q(date_start__lt=today)  # Удаляем события, которые начались ДО сегодня
        )

        # 3. Однодневные события с одинаковыми датами начала и окончания
        single_day_same_dates = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & Q(date_start=F("date_end"))
            & Q(date_start__lt=today)  # Удаляем события, которые были ДО сегодня
        )

        # Логируем каждый тип событий отдельно
        multi_day_list = list(
            multi_day_events.values("id", "name", "date_start", "date_end")
        )
        single_no_end_list = list(single_day_no_end.values("id", "name", "date_start"))
        single_same_dates_list = list(
            single_day_same_dates.values("id", "name", "date_start", "date_end")
        )

        logger.info(
            f"Found {len(multi_day_list)} multi-day events to delete: {multi_day_list}"
        )
        logger.info(
            f"Found {len(single_no_end_list)} single-day events (no end date) to delete: {single_no_end_list}"
        )
        logger.info(
            f"Found {len(single_same_dates_list)} single-day events (same dates) to delete: {single_same_dates_list}"
        )

        # Объединяем все запросы
        all_events = multi_day_events | single_day_no_end | single_day_same_dates

        # Удаляем события
        deleted_count, details = all_events.delete()

        logger.info(f"Successfully deleted {deleted_count} events with outdated dates")
        logger.info(f"Deletion details: {details}")
        return {
            "status": "success",
            "deleted_count": deleted_count,
            "details": {
                "multi_day_events": len(multi_day_list),
                "single_day_no_end": len(single_no_end_list),
                "single_day_same_dates": len(single_same_dates_list),
            },
        }

    except Exception as exc:
        logger.error(f"Error in delete_outdated_events: {exc}", exc_info=True)
        if self:  # Проверяем, что self существует (вызов через Celery)
            self.retry(exc=exc, countdown=3600)
        else:  # Прямой вызов
            raise


def setup_cleanup_schedule():
    """
    Настраивает расписание для очистки старых мероприятий
    Запускается ежедневно в 21:00 UTC (00:00 по московскому времени) для очистки истекших событий
    """
    try:
        logger.info("Setting up schedule for cleanup task")

        # Создаем или получаем расписание для ночной очистки (21:18 MSK)
        cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=21,
            minute=18,
            timezone="Europe/Moscow",
            defaults={
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
            },
        )

        # Создаем или обновляем задачу для очистки
        PeriodicTask.objects.update_or_create(
            name="Daily Cleanup Outdated Events",
            defaults={
                "task": "delete_outdated_events",
                "crontab": cleanup_schedule,
                "enabled": True,
                "kwargs": json.dumps({}),
                "description": "Ежедневная очистка устаревших мероприятий в 21:18 MSK",
            },
        )

        logger.info("Successfully set up schedule for cleanup task")
        return True

    except Exception as e:
        logger.error(f"Error setting up cleanup schedule: {str(e)}")
        raise


def setup_main_parsers_schedule():
    """
    Настраивает расписание запуска основных парсеров (KudaGo, Timepad, Telegram, VK)
    один раз в день утром в 5:00 UTC (8:00 MSK)
    """
    try:
        logger.info("Setting up schedule for main parsers")

        # Удаляем старые задачи если они существуют
        PeriodicTask.objects.filter(
            name__in=["Main Parsers Morning Run", "Main Parsers Evening Run"]
        ).delete()

        # Создаем или получаем расписание для утреннего запуска (8:00 MSK)
        daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=8,
            minute=0,
            timezone="Europe/Moscow",
            defaults={
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
            },
        )

        # Создаем или обновляем задачу для ежедневного запуска
        PeriodicTask.objects.update_or_create(
            name="Main Parsers Daily Run",
            defaults={
                "task": "run_main_parsers_simple",
                "crontab": daily_schedule,
                "enabled": True,
                "kwargs": json.dumps({}),
                "description": "Ежедневный запуск основных парсеров (KudaGo → Timepad → Telegram → VK) в 8:00 MSK - простая версия",
            },
        )

        logger.info("Successfully set up daily schedule for main parsers")
        return True

    except Exception as e:
        logger.error(f"Error setting up schedule for main parsers: {str(e)}")
        raise


@shared_task(name="setup_schedules")
def setup_all_schedules():
    """Настраивает все расписания для периодических задач"""
    try:
        logger.info("Setting up all schedules")
        setup_main_parsers_schedule()
        setup_cleanup_schedule()
        setup_notifications_schedule()  # Добавляем настройку расписания уведомлений
        logger.info("Successfully set up all schedules")
        return True
    except Exception as e:
        logger.error(f"Error setting up schedules: {str(e)}")
        return False


@shared_task(name="send_event_notifications")
def send_event_notifications():
    """
    Отправка уведомлений пользователям об их избранных событиях на сегодня.
    Включает как однодневные события, начинающиеся сегодня, так и многодневные события, активные сегодня.
    """
    logger.info("Starting event notifications task")

    try:
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
            """Отправка сообщения через Telegram HTTP API"""
            try:
                url = f"https://api.telegram.org/bot{settings.BOT_TOKEN}/sendMessage"
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
        logger.info(f"Поиск событий на {today}")

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

            from frameworks_and_drivers.django.parsing.data_manager.models import Like

        except ImportError as e:
            logger.error(f"Ошибка импорта моделей основного проекта: {e}")
            return {"status": "error", "message": "Модели основного проекта недоступны"}

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

        logger.info(f"Найдено {today_likes.count()} избранных событий на сегодня")

        # Группируем события по пользователям
        user_events = {}
        for like in today_likes:
            if like.user not in user_events:
                user_events[like.user] = []
            user_events[like.user].append(like.content)

        # Отправляем уведомления каждому пользователю
        sent_count = 0
        error_count = 0

        for user, events in user_events.items():
            try:
                # Получаем Telegram ID пользователя
                telegram_id = resolve_username_to_user_id(user.username)
                if not telegram_id:
                    logger.warning(
                        f"Не удалось получить Telegram ID для {user.username}"
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
                    message += f"🔗 <a href='{event_link}'>Открыть в приложении</a>\n\n"

                # Отправляем сообщение
                if send_telegram_message(telegram_id, message):
                    logger.info(f"Уведомление отправлено пользователю {user.username}")
                    sent_count += 1
                else:
                    logger.error(
                        f"Не удалось отправить уведомление пользователю {user.username}"
                    )
                    error_count += 1

            except Exception as e:
                logger.error(f"Ошибка обработки пользователя {user.username}: {e}")
                error_count += 1
                continue

        result = {
            "status": "success",
            "sent_notifications": sent_count,
            "errors": error_count,
            "total_users": len(user_events),
            "total_events": sum(len(events) for events in user_events.values()),
        }

        logger.info(f"Задача уведомлений завершена: {result}")
        return result

    except Exception as e:
        logger.error(f"Ошибка в задаче уведомлений: {e}")
        return {"status": "error", "message": str(e)}


def setup_notifications_schedule():
    """
    Настраивает расписание для отправки ежедневных уведомлений
    Запускается ежедневно в 6:00 UTC (9:00 MSK) одновременно с парсерами
    """
    try:
        logger.info("Setting up schedule for notifications task")

        # Создаем или получаем расписание для утренних уведомлений (9:00 MSK)
        notifications_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=9,
            minute=0,
            timezone="Europe/Moscow",
            defaults={
                "day_of_week": "*",
                "day_of_month": "*",
                "month_of_year": "*",
            },
        )

        # Создаем или обновляем задачу для уведомлений
        PeriodicTask.objects.update_or_create(
            name="Daily Event Notifications",
            defaults={
                "task": "send_event_notifications",
                "crontab": notifications_schedule,
                "enabled": True,
                "kwargs": json.dumps({}),
                "description": "Ежедневная отправка уведомлений об избранных событиях в 9:00 MSK",
            },
        )

        logger.info("Successfully set up schedule for notifications task")
        return True

    except Exception as e:
        logger.error(f"Error setting up notifications schedule: {str(e)}")
        raise
