#!/bin/bash

# Скрипт для очистки устаревших событий
# Запускается через cron

# Путь к проекту
PROJECT_DIR="/root/parsing_service"

# Логирование
LOG_FILE="/var/log/parsing_service_cleanup.log"

# Функция логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Starting cleanup task ==="

# Переходим в директорию проекта
cd "$PROJECT_DIR" || {
    log "ERROR: Cannot change to project directory $PROJECT_DIR"
    exit 1
}

# Запускаем очистку через Docker
log "Running cleanup command..."
docker compose exec -T django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_cleanup >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "SUCCESS: Cleanup completed successfully"
else
    log "ERROR: Cleanup failed"
    exit 1
fi

log "=== Cleanup task finished ==="
