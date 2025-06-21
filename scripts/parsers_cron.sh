#!/bin/bash

# Скрипт для запуска парсеров
# Запускается через cron

# Путь к проекту
PROJECT_DIR="/home/admin/parsing_service"

# Логирование
LOG_FILE="/home/admin/parsing_service_parsers.log"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Starting parsers task ==="

# Переходим в директорию проекта
cd "$PROJECT_DIR" || {
    log "ERROR: Cannot change to project directory $PROJECT_DIR"
    exit 1
}

# Запускаем парсеры через Django команду
log "Running parsers command..."
docker compose exec -T celery-worker-parsing python /app/src/frameworks_and_drivers/django/parsing/manage.py run_test_parser all >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "SUCCESS: Parsers completed successfully"
else
    log "ERROR: Parsers failed"
    exit 1
fi

log "=== Parsers task finished ==="
