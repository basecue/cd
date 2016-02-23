import logging
import colorama
import sys

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

actual_loglevel = 'info'


def logging_config(loglevel=None, control_command=False, perform=False, control_perform=False):
    global actual_loglevel
    if loglevel is None:
        loglevel = actual_loglevel
    else:
        actual_loglevel = loglevel

    loglevel = LOGLEVELS[loglevel]

    perform_formatter = logging.Formatter('perform [%(levelname)s] %(message)s')
    command_perform_formatter = logging.Formatter('command perform [%(levelname)s] %(message)s')
    control_formatter = logging.Formatter(colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s')
    command_control_perform_formatter = logging.Formatter(colorama.Fore.YELLOW + '[PERFORM]' + colorama.Fore.RESET + ' %(message)s')

    control_handler = logging.StreamHandler(stream=sys.stdout)
    control_handler.setLevel(loglevel)
    control_handler.formatter = control_formatter

    command_control_perform_handler = logging.StreamHandler(stream=sys.stdout)
    command_control_perform_handler.setLevel(loglevel)
    command_control_perform_handler.formatter = command_control_perform_formatter

    perform_handler = logging.StreamHandler(stream=sys.stdout)
    perform_handler.setLevel(loglevel)
    perform_handler.formatter = perform_formatter

    command_perform_handler = logging.StreamHandler(stream=sys.stdout)
    command_perform_handler.setLevel(loglevel)
    command_perform_handler.formatter = command_perform_formatter


    if control_command:
        command_logger = logging.getLogger('command')
        command_logger.setLevel(loglevel)
        for handler in command_logger.handlers:
            command_logger.removeHandler(handler)
        command_logger.addHandler(control_handler)

    if control_perform:
        command_logger = logging.getLogger('command')
        command_logger.setLevel(loglevel)
        for handler in command_logger.handlers:
            command_logger.removeHandler(handler)
        command_logger.addHandler(command_control_perform_handler)


    if perform:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in codev_logger.handlers:
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(perform_handler)

        command_logger = logging.getLogger('command')
        command_logger.setLevel(loglevel)
        for handler in command_logger.handlers:
            command_logger.removeHandler(handler)
        command_logger.addHandler(command_perform_handler)
    else:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in codev_logger.handlers:
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(control_handler)

logging_config()
