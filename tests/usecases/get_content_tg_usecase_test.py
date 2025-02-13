from datetime import datetime
from interface_adapters.presenters.schemas import ContentPydanticSchema


def test_execute_returns_valid_content(mock_gateway, mock_nlp_processor, usecase):
    # Настраиваем mock для gateway
    mock_gateway.fetch_content.return_value = "raw content"

    # Настраиваем mock для nlp_processor
    mock_nlp_processor.process.return_value = {
        "name": "Dynamic Name",
        "description": "Dynamic Description",
        "tags": ["dynamic_tag"],
        "image": b"dynamic_image_data",
        "contact": {"email": "dynamic@example.com"},
        "date_start": datetime(2023, 1, 1),
        "date_end": datetime(2023, 1, 2),
        "time": "18:00",
        "location": "Dynamic Location",
        "cost": 200,
    }

    # Выполняем usecase
    result = usecase.execute()

    # Проверяем, что результат имеет правильный тип
    assert isinstance(result, list)
    assert len(result) == 1

    # Проверяем, что объект внутри списка — это ContentPydanticSchema
    content = result[0]
    assert isinstance(content, ContentPydanticSchema)

    # Проверяем основные поля на наличие и типы
    assert isinstance(content.name, str)
    assert isinstance(content.description, str)
    assert isinstance(content.tags, list)
    assert all(isinstance(tag, str) for tag in content.tags)
    assert isinstance(content.image, bytes)
    assert isinstance(content.contact, dict)
    assert isinstance(content.date_start, datetime)
    assert isinstance(content.date_end, datetime)
    assert isinstance(content.time, str)
    assert isinstance(content.location, str)
    assert isinstance(content.cost, (int, float))


def test_execute_handles_missing_fields_gracefully(
    mock_gateway, mock_nlp_processor, usecase
):
    # Настраиваем mock для gateway
    mock_gateway.fetch_content.return_value = "raw content"

    # Настраиваем mock для nlp_processor с неполным содержимым
    mock_nlp_processor.process.return_value = {
        "name": "Partial Name",
        # Поля, которых нет, должны быть заменены значениями по умолчанию
    }

    # Выполняем usecase
    result = usecase.execute()

    # Проверяем, что результат имеет правильный тип
    assert isinstance(result, list)
    assert len(result) == 1

    content = result[0]
    assert isinstance(content, ContentPydanticSchema)

    # Проверяем, что значения по умолчанию установлены
    assert content.name == "Partial Name"
    assert isinstance(content.description, str)  # Должно быть значение по умолчанию
    assert isinstance(content.tags, list)
    assert isinstance(content.image, bytes)
    assert isinstance(content.contact, dict)
    assert isinstance(content.date_start, datetime)
    assert isinstance(content.date_end, datetime)
    assert isinstance(content.time, str)
    assert isinstance(content.location, str)
    assert isinstance(content.cost, (int, float))


def test_execute_handles_empty_raw_content(mock_gateway, mock_nlp_processor, usecase):
    # Настраиваем mock для gateway, возвращающий пустое содержимое
    mock_gateway.fetch_content.return_value = ""

    # Настраиваем mock для nlp_processor, возвращающий пустой словарь
    mock_nlp_processor.process.return_value = {}

    # Выполняем usecase
    result = usecase.execute()

    # Проверяем, что результат содержит значение по умолчанию
    assert isinstance(result, list)
    assert len(result) == 1

    content = result[0]
    assert isinstance(content, ContentPydanticSchema)

    # Проверяем, что все значения имеют типы по умолчанию
    assert isinstance(content.name, str)
    assert isinstance(content.description, str)
    assert isinstance(content.tags, list)
    assert isinstance(content.image, bytes)
    assert isinstance(content.contact, dict)
    assert isinstance(content.date_start, datetime)
    assert isinstance(content.date_end, datetime)
    assert isinstance(content.time, str)
    assert isinstance(content.location, str)
    assert isinstance(content.cost, (int, float))
