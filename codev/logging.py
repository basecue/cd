import logging
import colorama
import sys

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

actual_loglevel = 'info'


def logging_config(loglevel=None, control_command=False, perform=False, control_perform=False):
    """
    :param loglevel:
    :param control_command:
    :param perform:
    :param control_perform:
    :return:
    """
    # TODO RED ERRORS
    global actual_loglevel

    if loglevel is None:
        loglevel = actual_loglevel
    else:
        actual_loglevel = loglevel

    loglevel = LOGLEVELS[loglevel]

    perform_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    perform_debug_formatter = logging.Formatter('[%(levelname)s]' + colorama.Fore.CYAN + ' [DEBUG] %(message)s')
    perform_command_formatter = logging.Formatter('[%(levelname)s] %(message)s')

    control_formatter = logging.Formatter(colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s')
    control_debug_formatter = logging.Formatter(colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s]' + colorama.Fore.CYAN + ' [DEBUG] %(message)s' + colorama.Fore.RESET)
    control_command_perform_formatter = logging.Formatter(colorama.Fore.YELLOW + '[PERFORM]' + colorama.Fore.RESET + ' %(message)s')

    control_handler = logging.StreamHandler(stream=sys.stdout)
    control_handler.setLevel(loglevel)
    control_handler.formatter = control_formatter

    control_debug_handler = logging.StreamHandler(stream=sys.stdout)
    control_debug_handler.setLevel(loglevel)
    control_debug_handler.formatter = control_debug_formatter

    control_command_perform_handler = logging.StreamHandler(stream=sys.stdout)
    control_command_perform_handler.setLevel(loglevel)
    control_command_perform_handler.formatter = control_command_perform_formatter

    perform_handler = logging.StreamHandler(stream=sys.stdout)
    perform_handler.setLevel(loglevel)
    perform_handler.formatter = perform_formatter

    perform_command_handler = logging.StreamHandler(stream=sys.stdout)
    perform_command_handler.setLevel(logging.ERROR)
    perform_command_handler.formatter = perform_command_formatter

    perform_debug_handler = logging.StreamHandler(stream=sys.stdout)
    perform_debug_handler.setLevel(loglevel)
    perform_debug_handler.formatter = perform_debug_formatter

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
        command_logger.addHandler(control_command_perform_handler)

    if perform:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in codev_logger.handlers:
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(perform_handler)

        debug_logger = logging.getLogger('debug')
        debug_logger.setLevel(loglevel)
        for handler in debug_logger.handlers:
            debug_logger.removeHandler(handler)
        debug_logger.addHandler(perform_debug_handler)

        command_logger = logging.getLogger('command')
        command_logger.setLevel(logging.ERROR)
        for handler in command_logger.handlers:
            command_logger.removeHandler(handler)
        command_logger.addHandler(perform_command_handler)
    else:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in codev_logger.handlers:
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(control_handler)

        debug_logger = logging.getLogger('debug')
        debug_logger.setLevel(loglevel)
        for handler in debug_logger.handlers:
            debug_logger.removeHandler(handler)
        debug_logger.addHandler(control_debug_handler)


logging_config()
