# Рефакторированная архитектура NLPProcessor

## Обзор

Архитектура `NLPProcessor` была полностью рефакторирована для повышения гибкости и масштабируемости. Теперь она использует паттерн Dependency Injection и позволяет легко менять AI провайдеров и обработчики промптов.

## Основные компоненты

### 1. Интерфейсы

- **`AIProviderInterface`** - интерфейс для AI провайдеров
- **`PromptProcessorInterface`** - интерфейс для обработчиков промптов
- **`NLPProcessorBase`** - базовый класс для NLP процессоров

### 2. Провайдеры AI

- **`ThebAIProvider`** - провайдер для ThebAI API
- **`OpenRouterProvider`** - провайдер для OpenRouter API

### 3. Обработчики промптов

- **`YamlPromptProcessor`** - обработчик промптов на основе YAML конфигурации

### 4. Фабрика

- **`NLPProcessorFactory`** - фабрика для создания экземпляров NLPProcessor

## Использование

### Базовое использование

```python
from frameworks_and_drivers.gateways.nlp_gateway.nlp_processor_factory import NLPProcessorFactory

# Создание NLPProcessor с OpenRouter (по умолчанию)
nlp_processor = NLPProcessorFactory.create_nlp_processor()

# Создание NLPProcessor с ThebAI
nlp_processor = NLPProcessorFactory.create_nlp_processor(provider_name="thebai")

# Обработка текста
result = nlp_processor.process("Ваш текст для обработки")
```

### Использование с пользовательской конфигурацией

```python
# Создание с пользовательской конфигурацией провайдера
provider_config = {
    "api_key": "your_custom_api_key",
    "model": "gpt-4"
}

nlp_processor = NLPProcessorFactory.create_nlp_processor(
    provider_name="openrouter",
    provider_config=provider_config
)
```

### Использование в Use Cases

```python
from interface_adapters.controlles.factory import UseCaseFactory

# Создание use case с выбранным провайдером
usecase = UseCaseFactory.get_tg_content_usecase(ai_provider="thebai")
```

### Добавление нового AI провайдера

```python
from interface_adapters.gateways.ai_provider_base.ai_provider_interface import AIProviderInterface

class MyCustomProvider(AIProviderInterface):
    def send_request(self, prompt: str, **kwargs) -> str:
        # Ваша реализация
        pass

    def get_provider_name(self) -> str:
        return "my_custom_provider"

    def is_available(self) -> bool:
        return True

# Регистрация нового провайдера
NLPProcessorFactory.register_provider("my_custom", MyCustomProvider)

# Использование
nlp_processor = NLPProcessorFactory.create_nlp_processor(provider_name="my_custom")
```

## Преимущества новой архитектуры

1. **Гибкость** - легко менять AI провайдеров без изменения основного кода
2. **Масштабируемость** - простое добавление новых провайдеров и обработчиков
3. **Тестируемость** - возможность мокирования провайдеров для тестирования
4. **Разделение ответственности** - каждый компонент отвечает за свою область
5. **Конфигурируемость** - возможность настройки провайдеров через параметры

## Миграция со старой архитектуры

### Старый код:
```python
nlp_processor = NLPProcessor()
```

### Новый код:
```python
nlp_processor = NLPProcessorFactory.create_nlp_processor()
```

Или с указанием конкретного провайдера:
```python
nlp_processor = NLPProcessorFactory.create_nlp_processor(provider_name="thebai")
```
