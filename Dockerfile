FROM python:3.11

# Установка системных пакетов
RUN apt-get update && apt-get install -y libpq-dev && apt-get clean

# Установка рабочего каталога
WORKDIR /app

# Копирование зависимостей
COPY requirements.txt /app/

# Установка зависимостей Python
RUN pip install --no-cache-dir -r requirements.txt

# Копирование всего проекта
COPY . /app/

# Убедимся, что есть права на выполнение
RUN chmod +x /app

# Определение команды по умолчанию
CMD ["python", "src/frameworks_and_drivers/django/parsing/manage.py"]
