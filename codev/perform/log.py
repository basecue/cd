import logging
import sys

from colorama import Fore as color

from codev.core.log import LOGLEVELS, error_filter, info_filter, debug_filter


def logging_config(loglevel=None):
    """
    :param loglevel:
    :param control_command:
    :param perform:
    :param control_perform:
    :return:
    """
    global actual_loglevel

    if loglevel is None:
        loglevel = actual_loglevel
    else:
        actual_loglevel = loglevel

    loglevel = LOGLEVELS[loglevel]

    shell_formatter = logging.Formatter(
        color.RESET + '%(message)s'
    )

    perform_error_formatter = logging.Formatter(
        color.RED + '[%(levelname)s] %(message)s' + color.RESET
    )

    perform_info_formatter = logging.Formatter(
        color.RESET + '[%(levelname)s] %(message)s'
    )

    perform_formatter = logging.Formatter(
        color.RESET + '[%(levelname)s] <%(name)s:%(lineno)s> %(message)s'
    )

    perform_debug_formatter = logging.Formatter(
        color.RESET + '[%(levelname)s]' + color.MAGENTA + ' [DEBUG] %(message)s' + color.RESET
    )
    perform_command_output_formatter = logging.Formatter(
        color.RESET + '[%(levelname)s]' + color.GREEN + ' [OUTPUT] %(message)s' + color.RESET
    )

    shell_handler = logging.StreamHandler(stream=sys.stdout)
    shell_handler.setLevel(logging.DEBUG)
    shell_handler.formatter = shell_formatter

    perform_error_handler = logging.StreamHandler(stream=sys.stderr)
    perform_error_handler.setLevel(logging.ERROR)
    perform_error_handler.formatter = perform_error_formatter
    perform_error_handler.addFilter(error_filter)

    perform_info_handler = logging.StreamHandler(stream=sys.stdout)
    perform_info_handler.setLevel(logging.INFO)
    perform_info_handler.formatter = perform_info_formatter
    perform_info_handler.addFilter(info_filter)

    perform_handler = logging.StreamHandler(stream=sys.stdout)
    perform_handler.setLevel(logging.DEBUG)
    perform_handler.formatter = perform_formatter
    perform_handler.addFilter(debug_filter)

    perform_command_output_handler = logging.StreamHandler(stream=sys.stdout)
    perform_command_output_handler.setLevel(loglevel)
    perform_command_output_handler.formatter = perform_command_output_formatter

    perform_debug_handler = logging.StreamHandler(stream=sys.stdout)
    perform_debug_handler.setLevel(loglevel)
    perform_debug_handler.formatter = perform_debug_formatter

    codev_logger = logging.getLogger('codev')
    codev_logger.setLevel(loglevel)
    for handler in list(codev_logger.handlers):
        codev_logger.removeHandler(handler)
    codev_logger.addHandler(perform_handler)
    codev_logger.addHandler(perform_info_handler)
    codev_logger.addHandler(perform_error_handler)

    debug_logger = logging.getLogger('debug')
    debug_logger.setLevel(loglevel)
    for handler in list(debug_logger.handlers):
        debug_logger.removeHandler(handler)
    debug_logger.addHandler(perform_debug_handler)

    command_output_logger = logging.getLogger('command_output')
    command_output_logger.setLevel(loglevel)
    for handler in list(command_output_logger.handlers):
        command_output_logger.removeHandler(handler)
    command_output_logger.addHandler(perform_command_output_handler)
