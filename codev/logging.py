# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import logging
import colorama
import sys

LOGLEVELS = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
}

actual_loglevel = 'info'


class InfoFilter(logging.Filter):
    def filter(self, record):
        if record.levelno >= logging.INFO:
            return True

info_filter = InfoFilter()


class DebugFilter(logging.Filter):
    def filter(self, record):
        if record.levelno == logging.DEBUG:
            return True


debug_filter = DebugFilter()


def logging_config(loglevel=None, perform=False, control_perform=False):
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

    control_perform_loglevel = logging.DEBUG if control_perform else logging.INFO

    loglevel = LOGLEVELS[loglevel]

    perform_info_formatter = logging.Formatter(
        colorama.Fore.RESET + '[%(levelname)s] %(message)s'
    )

    perform_formatter = logging.Formatter(
        colorama.Fore.RESET + '[%(levelname)s] <%(name)s:%(lineno)s> %(message)s'
    )

    perform_debug_formatter = logging.Formatter(
        colorama.Fore.RESET + '[%(levelname)s]' + colorama.Fore.MAGENTA + ' [DEBUG] %(message)s'
    )
    perform_command_output_formatter = logging.Formatter(
        colorama.Fore.RESET + '[%(levelname)s]' + colorama.Fore.GREEN + ' [OUTPUT] %(message)s' + colorama.Fore.RESET
    )

    control_info_formatter = logging.Formatter(
        colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s'
    )

    control_formatter = logging.Formatter(
        colorama.Fore.BLUE + '[CONTROL]' + colorama.Fore.RESET + ' [%(levelname)s] <%(name)s:%(lineno)s> %(message)s'
    )

    control_debug_formatter = logging.Formatter(
        colorama.Fore.BLUE +
        '[CONTROL]' + colorama.Fore.RESET +
        ' [%(levelname)s]' +
        colorama.Fore.MAGENTA +
        ' [DEBUG] %(message)s' +
        colorama.Fore.RESET
    )
    control_command_perform_formatter = logging.Formatter(
        colorama.Fore.YELLOW + '[PERFORM]' + colorama.Fore.RESET + ' %(message)s'
    )
    control_command_output_formatter = logging.Formatter(
        colorama.Fore.BLUE +
        '[CONTROL]' +
        colorama.Fore.RESET +
        ' [%(levelname)s]' +
        colorama.Fore.CYAN +
        ' [OUTPUT] %(message)s' +
        colorama.Fore.RESET
    )

    control_info_handler = logging.StreamHandler(stream=sys.stdout)
    control_info_handler.setLevel(loglevel)
    control_info_handler.formatter = control_info_formatter
    control_info_handler.addFilter(info_filter)

    control_handler = logging.StreamHandler(stream=sys.stdout)
    control_handler.setLevel(loglevel)
    control_handler.formatter = control_formatter
    control_handler.addFilter(debug_filter)

    control_debug_handler = logging.StreamHandler(stream=sys.stdout)
    control_debug_handler.setLevel(loglevel)
    control_debug_handler.formatter = control_debug_formatter

    control_command_perform_handler = logging.StreamHandler(stream=sys.stdout)
    control_command_perform_handler.setLevel(control_perform_loglevel)
    control_command_perform_handler.formatter = control_command_perform_formatter

    control_command_output_handler = logging.StreamHandler(stream=sys.stdout)
    control_command_output_handler.setLevel(loglevel)
    control_command_output_handler.formatter = control_command_output_formatter

    perform_info_handler = logging.StreamHandler(stream=sys.stdout)
    perform_info_handler.setLevel(loglevel)
    perform_info_handler.formatter = perform_info_formatter
    perform_info_handler.addFilter(info_filter)

    perform_handler = logging.StreamHandler(stream=sys.stdout)
    perform_handler.setLevel(loglevel)
    perform_handler.formatter = perform_formatter
    perform_handler.addFilter(debug_filter)

    perform_command_output_handler = logging.StreamHandler(stream=sys.stdout)
    perform_command_output_handler.setLevel(loglevel)
    perform_command_output_handler.formatter = perform_command_output_formatter

    perform_debug_handler = logging.StreamHandler(stream=sys.stdout)
    perform_debug_handler.setLevel(loglevel)
    perform_debug_handler.formatter = perform_debug_formatter

    if perform:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in list(codev_logger.handlers):
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(perform_handler)
        codev_logger.addHandler(perform_info_handler)

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
    else:
        codev_logger = logging.getLogger('codev')
        codev_logger.setLevel(loglevel)
        for handler in list(codev_logger.handlers):
            codev_logger.removeHandler(handler)
        codev_logger.addHandler(control_handler)
        codev_logger.addHandler(control_info_handler)

        debug_logger = logging.getLogger('debug')
        debug_logger.setLevel(loglevel)
        for handler in list(debug_logger.handlers):
            debug_logger.removeHandler(handler)
        debug_logger.addHandler(control_debug_handler)

        command_output_logger = logging.getLogger('command_output')
        command_output_logger.setLevel(loglevel)
        for handler in list(command_output_logger.handlers):
            command_output_logger.removeHandler(handler)
        command_output_logger.addHandler(control_command_output_handler)

        if control_perform:
            command_logger = logging.getLogger('command')
            command_logger.setLevel(control_perform_loglevel)
            for handler in list(command_logger.handlers):
                command_logger.removeHandler(handler)
            command_logger.addHandler(control_command_perform_handler)
        else:
            command_logger = logging.getLogger('command')
            command_logger.setLevel(loglevel)
            for handler in list(command_logger.handlers):
                command_logger.removeHandler(handler)
            command_logger.addHandler(control_command_perform_handler)

logging_config()
