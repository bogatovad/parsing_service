#!/bin/bash

# Скрипт для отправки уведомлений пользователям
# Запускается через cron

# Путь к проекту
PROJECT_DIR="/home/admin/parsing_service"

# Логирование
LOG_FILE="/home/admin/parsing_service_notifications.log"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Starting notifications task ==="

# Переходим в директорию проекта
cd "$PROJECT_DIR" || {
    log "ERROR: Cannot change to project directory $PROJECT_DIR"
    exit 1
}

# Запускаем отправку уведомлений через Django команду
log "Running notifications command..."
docker compose exec -T celery-worker-parsing python /app/src/frameworks_and_drivers/django/parsing/manage.py send_notifications >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "SUCCESS: Notifications completed successfully"
else
    log "ERROR: Notifications failed"
    exit 1
fi

log "=== Notifications task finished ==="
