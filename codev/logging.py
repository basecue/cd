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
    },
    loggers={
        'codev.executors': {
            'handlers': ['console'],
            'level': logging.INFO
        },
        'codev.deployment': {
            'handlers': ['console'],
            'level': logging.INFO
        }
    }
)

dictConfig(logging_config)

