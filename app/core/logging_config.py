import logging
import logging.config
import sys


def setup_logging() -> None:
    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,

        "formatters": {
            "standard": {
                "format": (
                    "%(asctime)s | %(levelname)s | "
                    "%(name)s | %(message)s"
                ),
            },
        },

        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "standard",
                "level": "INFO",
            },
        },

        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
    })