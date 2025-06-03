# Базовая конфигурация логирования
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "level": "INFO",
        },
        "file": {
            "class": "logging.FileHandler",
            "filename": "parsing_service.log",
            "formatter": "verbose",
            "level": "DEBUG",
        },
    },
    "loggers": {
        "": {  # Root logger
            "handlers": ["console", "file"],
            "level": "INFO",
        },
        "nlp_processor": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "telegram": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "vk": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
        "kudago": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
