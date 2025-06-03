from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "frameworks_and_drivers.django.parsing.parsing.settings"
)

app = Celery("parsing_service")

app.config_from_object("django.conf:settings", namespace="CELERY")

# Явно указываем пакеты для поиска задач
app.autodiscover_tasks(["frameworks_and_drivers.django.parsing"])

# Импортируем задачи
