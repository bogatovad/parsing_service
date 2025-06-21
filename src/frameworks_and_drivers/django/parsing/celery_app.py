from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)

app = Celery("parsing_service")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Автодискавери задач из Django приложений
app.autodiscover_tasks()

# Явно импортируем модуль с задачами - это критически важно!

# Также убедимся что задачи зарегистрированы
app.autodiscover_tasks(["frameworks_and_drivers.django.parsing"])
