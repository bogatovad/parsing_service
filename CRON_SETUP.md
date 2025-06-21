# Настройка Cron для автоматизации задач

Вместо сложного Celery Beat можно использовать простой и надежный cron.

## Преимущества cron

- ✅ Простота настройки
- ✅ Надежность
- ✅ Стандартный инструмент Linux
- ✅ Легкое отслеживание и отладка
- ✅ Независимость от Celery

## Настройка

### 1. Подготовка скрипта

Скрипт уже создан: `scripts/cleanup_cron.sh`

Сделайте его исполняемым:
```bash
chmod +x /root/parsing_service/scripts/cleanup_cron.sh
```

### 2. Тестирование команды

Сначала проверьте, что команда работает:
```bash
# Dry run (покажет что будет удалено)
docker compose exec django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_cleanup --dry-run

# Реальное выполнение
docker compose exec django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_cleanup
```

### 3. Настройка cron

Откройте crontab:
```bash
crontab -e
```

Добавьте строку для ежедневной очистки в полночь:
```cron
# Очистка устаревших событий каждый день в 00:01
1 0 * * * /root/parsing_service/scripts/cleanup_cron.sh
```

Или для парсеров (если нужно):
```cron
# Запуск парсеров каждый день в 9:00
0 9 * * * cd /root/parsing_service && docker compose exec -T django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_test_parser all >> /var/log/parsing_service_parsers.log 2>&1
```

### 4. Проверка cron

Проверьте, что cron настроен:
```bash
crontab -l
```

Проверьте статус cron службы:
```bash
systemctl status cron
```

## Логирование

Логи записываются в:
- Очистка: `/var/log/parsing_service_cleanup.log`
- Парсеры: `/var/log/parsing_service_parsers.log`

Просмотр логов:
```bash
tail -f /var/log/parsing_service_cleanup.log
```

## Мониторинг

Для проверки работы cron:
```bash
# Проверка последних запусков cron
grep "cleanup" /var/log/syslog

# Проверка размера логов
ls -lh /var/log/parsing_service_*.log
```

## Устранение неполадок

1. **Cron не запускается**: Проверьте синтаксис в crontab
2. **Нет логов**: Убедитесь что путь к логам корректный
3. **Ошибки Docker**: Проверьте что Docker compose работает
4. **Права доступа**: Убедитесь что скрипт исполняемый

## Альтернативная настройка (прямо в cron)

Если не хотите создавать скрипт, можно добавить прямо в cron:
```cron
# Очистка устаревших событий каждый день в 00:01
1 0 * * * cd /root/parsing_service && docker compose exec -T django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_cleanup >> /var/log/parsing_service_cleanup.log 2>&1
```

## Тестирование прямо сейчас

Протестируйте команду очистки:
```bash
docker compose exec django python /app/src/frameworks_and_drivers/django/parsing/manage.py run_cleanup --dry-run
```
