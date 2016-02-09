import logging


control_config = dict(
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
    }
)


perform_config = dict(
    version=1,
    formatters={
        'perform': {
            'format':
            '[%(levelname)s] %(message)s'
        }
    },
    handlers={
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'perform',
            'level': logging.INFO
        },
        'debug_console': {
            'class': 'logging.StreamHandler',
            'formatter': 'perform',
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
        }
    }
)


class CommandLogger(logging.Logger):
    def __init__(self):
        super(CommandLogger, self).__init__('control', logging.INFO)

    def set_control_perform_mode(self):
        control_perform_handler = logging.StreamHandler()
        control_perform_handler.formatter = logging.Formatter('[PERFORM] %(message)s')
        self.addHandler(control_perform_handler)

command_logger = CommandLogger()
