import logging
from logging.config import dictConfig

logging_config = dict(
    version=1,
    formatters={
        'control': {
            'format':
            '[CONTROL] [%(levelname)s] %(message)s'
        }
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'control',
            'level': logging.INFO
        },
        'debug_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'control',
            'level': logging.DEBUG
        },
    },
    loggers={
        'codev.executors': {
            'handlers': ['console'],
            'level': logging.INFO
        },
        'codev.environment': {
            'handlers': ['console'],
            'level': logging.INFO
        },
        'codev.performers': {
            'handlers': ['console'],
            'level': logging.DEBUG
        }
    }
)

dictConfig(logging_config)

