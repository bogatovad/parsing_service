from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Явно импортируем задачи из tasks.py
from frameworks_and_drivers.django.parsing.tasks import (
    delete_outdated_events,
)  # Это зарегистрирует задачу

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)

app = Celery("parsing_service")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Автодискавери задач из Django приложений
app.autodiscover_tasks()

# Также убедимся что задачи зарегистрированы
app.autodiscover_tasks(["frameworks_and_drivers.django.parsing"])

print(delete_outdated_events)
