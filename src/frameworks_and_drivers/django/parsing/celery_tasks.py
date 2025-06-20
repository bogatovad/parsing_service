import logging
from celery import chain, shared_task
from datetime import timedelta
from django.utils import timezone
from django.db.models import F, Q
from frameworks_and_drivers.django.parsing.celery_app import app
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

logger = logging.getLogger(__name__)

# Создаем фабрику и контроллеры один раз при загрузке модуля
factory_usecase = UseCaseFactory()
controller_timepad = GetContentTimepadController(usecase_factory=factory_usecase)
controller_tg = GetContentTgController(usecase_factory=factory_usecase)
controller_kuda_go = GetContentKudaGoController(usecase_factory=factory_usecase)
controller_vk = GetContentVKController(usecase_factory=factory_usecase)
controller_place = PlacesController(usecase_factory=factory_usecase)


@app.task(name="parse_telegram")
def parse_telegram():
    """Запуск парсера Telegram"""
    try:
        controller_tg.get_content()
        logger.info("Telegram parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Telegram parser: {str(e)}")
        return False


@app.task(name="parse_vk")
def parse_vk():
    """Запуск парсера VK"""
    try:
        controller_vk.get_content()
        logger.info("VK parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in VK parser: {str(e)}")
        return False


@app.task(name="parse_timepad")
def parse_timepad():
    """Запуск парсера Timepad"""
    try:
        controller_timepad.get_content()
        logger.info("Timepad parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Timepad parser: {str(e)}")
        return False


@app.task(name="parse_kudago")
def parse_kudago():
    """Запуск парсера KudaGo"""
    try:
        controller_kuda_go.get_content()
        logger.info("KudaGo parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in KudaGo parser: {str(e)}")
        return False


@app.task(name="parse_places")
def parse_places():
    """Запуск парсера Places"""
    try:
        controller_place.get_content()
        logger.info("Places parser finished successfully")
        return True
    except Exception as e:
        logger.error(f"Error in Places parser: {str(e)}")
        return False


@app.task(name="run_all_parsers")
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


@app.task(name="run_main_parsers")
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


def setup_cleanup_schedule():
    """
    Настраивает расписание для очистки старых мероприятий
    Запускается ежедневно в 21:00 UTC (00:00 по московскому времени) для очистки истекших событий
    """
    try:
        logger.info("Setting up schedule for cleanup task")

        # Создаем или получаем расписание для ночной очистки (21:00 UTC = 00:00 MSK)
        cleanup_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=21,
            minute=0,
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
                "description": "Ежедневная очистка устаревших мероприятий в 21:00 UTC (00:00 MSK)",
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
    один раз в день утром в 6:00 UTC (9:00 MSK)
    """
    try:
        logger.info("Setting up schedule for main parsers")

        # Удаляем старые задачи если они существуют
        PeriodicTask.objects.filter(
            name__in=["Main Parsers Morning Run", "Main Parsers Evening Run"]
        ).delete()

        # Создаем или получаем расписание для утреннего запуска (6:00 UTC = 9:00 MSK)
        daily_schedule, _ = CrontabSchedule.objects.get_or_create(
            hour=6,
            minute=0,
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
                "description": "Ежедневный запуск основных парсеров (KudaGo → Timepad → Telegram → VK) в 6:00 UTC (9:00 MSK) - простая версия",
            },
        )

        logger.info("Successfully set up daily schedule for main parsers")
        return True

    except Exception as e:
        logger.error(f"Error setting up schedule for main parsers: {str(e)}")
        raise


@app.task(name="setup_schedules")
def setup_all_schedules():
    """Настраивает все расписания для периодических задач"""
    try:
        logger.info("Setting up all schedules")
        setup_main_parsers_schedule()
        setup_cleanup_schedule()  # Добавляем настройку расписания очистки
        logger.info("Successfully set up all schedules")
        return True
    except Exception as e:
        logger.error(f"Error setting up schedules: {str(e)}")
        return False


@app.task(name="test_parser")
def test_parser(parser_name: str):
    """
    Тестовый запуск парсера по имени

    :param parser_name: Имя парсера (tg, vk, timepad, kudago, places, all)
    """
    parser_name = parser_name.lower()
    if parser_name not in PARSER_TASKS:
        logger.error(
            f"Unknown parser: {parser_name}. Available parsers: {', '.join(PARSER_TASKS.keys())}"
        )
        return False

    task = PARSER_TASKS[parser_name]
    return task.delay()


@shared_task(bind=True, max_retries=3)
def delete_outdated_events(self):
    """Task to delete old events based on date conditions."""
    try:
        logger.info("Starting deletion of outdated events")

        # Используем текущую дату в UTC
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)

        logger.info(f"Deleting events before or on {yesterday} (UTC). Today is {today}")

        # 1. События с указанными датами начала и окончания (многодневные, которые уже завершились)
        multi_day_events = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & ~Q(date_start=F("date_end"))  # Исключаем однодневные события
            & Q(date_end__lte=yesterday)  # Изменено с __lt на __lte (включительно)
        )

        # 2. Однодневные события без даты окончания
        single_day_no_end = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=True)
            & Q(date_start__lte=yesterday)  # Изменено с __lt на __lte (включительно)
        )

        # 3. Однодневные события с одинаковыми датами начала и окончания
        single_day_same_dates = Content.objects.filter(
            Q(date_start__isnull=False)
            & Q(date_end__isnull=False)
            & Q(date_start=F("date_end"))
            & Q(date_start__lte=yesterday)  # Изменено с __lt на __lte (включительно)
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
        self.retry(exc=exc, countdown=3600)


# Обновляем словарь доступных задач
PARSER_TASKS = {
    "tg": parse_telegram,
    "vk": parse_vk,
    "timepad": parse_timepad,
    "kudago": parse_kudago,
    "places": parse_places,
    "all": run_all_parsers,
    "main": run_main_parsers,
    "setup_schedules": setup_all_schedules,  # Добавляем задачу настройки расписания
    "cleanup": delete_outdated_events,  # Добавляем задачу очистки для ручного запуска
}
