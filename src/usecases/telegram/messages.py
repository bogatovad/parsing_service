class Message:
    INIT = "[ИНИЦИАЛИЗАЦИЯ] UseCase для получения контента из Telegram и обработки NLP инициализирован."
    START_GATEWAY_PROCESS = "[ВЫПОЛНЕНИЕ] Получаем данные из gateway."
    END_GATEWAY_PROCESS = "[ВЫПОЛНЕНИЕ] Получены данные от gateway."
    CREATE_SCHEMA = "[РЕЗУЛЬТАТ] Создан объект ContentPydanticSchema."
    ERROR_CREATE_SCHEMA = "[ОБРАБОТКА] Ошибка при создании схемы."
