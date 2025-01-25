# parsing_service

Для запуска сервиса выполнить команду

docker-compose down && docker-compose up -d

Затем можно посмотреть логи воркера и увидеть что там отрабатывает периодическая таска

docker logs -f parsing_service-celery-worker-1