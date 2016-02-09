import logging

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}


def control_config(loglevel):
    return dict(
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
                'level': loglevel
            },
        },
        loggers={
            'codev.executors': {
                'handlers': ['console'],
                'level': loglevel
            },
            'codev.environment': {
                'handlers': ['console'],
                'level': loglevel
            },
            'codev.performers': {
                'handlers': ['console'],
                'level': loglevel
            }
        }
    )


def perform_config(loglevel):
    return dict(
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
                'level': loglevel
            },
        },
        loggers={
            'codev.executors': {
                'handlers': ['console'],
                'level': loglevel
            },
            'codev.environment': {
                'handlers': ['console'],
                'level': loglevel
            },
            'codev.performers': {
                'handlers': ['console'],
                'level': loglevel
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
