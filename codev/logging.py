import logging
from logging.config import dictConfig
import colorama

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

actual_loglevel = 'info'


def logging_config(loglevel=None, control_command=False, perform=False, control_perform=False):
    print(10*'#')
    print(loglevel, perform, control_perform)
    global actual_loglevel
    if loglevel is None:
        loglevel = actual_loglevel
    else:
        actual_loglevel = loglevel
    print(loglevel, perform, control_perform)

    loglevel = LOGLEVELS[loglevel]
    config = dict(
        version=1,
        formatters=dict(
            control=dict(
                format=colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s'
            ),
            perform=dict(
                format='perform [%(levelname)s] %(message)s'
            ),
            command_perform=dict(
                format='command perform [%(levelname)s] %(message)s'
            ),
            command_control_perform=dict(
                format=colorama.Fore.YELLOW + '[PERFORM]' + colorama.Fore.RESET + ' %(message)s'
            )
        ),
        handlers=dict(
            control={
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'control',
                'level': loglevel
            },
            perform={
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'perform',
                'level': loglevel
            },
            command_perform={
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'command_perform',
                'level': loglevel
            },
            command_control_perform={
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout',
                'formatter': 'command_control_perform',
                'level': loglevel
            },
        )
    )
    control_config = {
        'loggers': {
            'codev': {
                'level': loglevel,
                'handlers': ['control'],
            }
        }
    }
    if control_command:
        control_config['loggers']['command'] = {
            'level': loglevel,
            'handlers': ['control']
        }

    if control_perform:
        control_config['loggers']['command'] = {
            'level': loglevel,
            'handlers': ['command_control_perform']
        }

    perform_config = {
        'loggers': {
            'codev': {
                'level': loglevel,
                'handlers': ['perform'],
            },
            'command': {
                'level': loglevel,
                'handlers': ['command_perform']
            }
        }
    }
    if perform:
        config.update(perform_config)
    else:
        config.update(control_config)

    dictConfig(config)

logging_config()

command_logger = logging.getLogger('command')
