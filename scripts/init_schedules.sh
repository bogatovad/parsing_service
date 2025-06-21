#!/bin/bash

# Скрипт для инициализации расписания задач
# Запускается после развертывания контейнеров

set -e

echo "🚀 Инициализация расписания задач..."

# Ждем, пока база данных будет готова
echo "⏳ Ожидание готовности базы данных..."
python /app/src/frameworks_and_drivers/django/parsing/manage.py wait_for_db

# Применяем миграции
echo "📊 Применение миграций базы данных..."
python /app/src/frameworks_and_drivers/django/parsing/manage.py migrate

# Настраиваем расписание задач
echo "📅 Настройка расписания задач..."
python /app/src/frameworks_and_drivers/django/parsing/manage.py setup_schedule

echo "✅ Инициализация завершена успешно!"
echo ""
echo "📋 Настроенные задачи:"
echo "  📅 Парсеры: ежедневно в 9:00 MSK"
echo "  🧹 Очистка: ежедневно в 00:00 MSK"
echo ""
