#!/bin/bash

# Скрипт для развертывания системы парсинга с настройкой расписания

set -e

echo "🚀 Развертывание системы парсинга афиши..."
echo ""

# Проверяем наличие сети
if ! docker network ls | grep -q "afisha"; then
    echo "📡 Создание Docker сети 'afisha'..."
    docker network create afisha
else
    echo "📡 Сеть 'afisha' уже существует"
fi

# Сборка образов
echo "🔨 Сборка Docker образов..."
docker compose build

# Инициализация расписания
echo "📅 Инициализация расписания задач..."
docker compose --profile init up schedule-init

# Запуск основных сервисов
echo "🎯 Запуск Celery сервисов..."
docker compose up -d celery-worker-parsing celery-beat-parsing

echo ""
echo "✅ Развертывание завершено успешно!"
echo ""
echo "📋 Запущенные сервисы:"
echo "  🔄 celery-worker-parsing - обработчик задач"
echo "  ⏰ celery-beat-parsing - планировщик задач"
echo ""
echo "📅 Настроенное расписание:"
echo "  📊 Парсеры: ежедневно в 9:00 MSK"
echo "  🧹 Очистка: ежедневно в 00:00 MSK"
echo ""
echo "🔍 Проверка статуса:"
echo "  docker-compose ps"
echo "  docker-compose logs -f celery-beat-parsing"
echo ""
