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


def logging_config(loglevel=None, control_command=False, perform=False, control_perform=False, perform_command_loglevel=None):
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

    if perform_command_loglevel in LOGLEVELS:
        perform_command_loglevel = LOGLEVELS[perform_command_loglevel]

    else:
        perform_command_loglevel = logging.ERROR

    perform_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    perform_debug_formatter = logging.Formatter('[%(levelname)s]' + colorama.Fore.CYAN + ' [DEBUG] %(message)s')
    perform_command_formatter = logging.Formatter(colorama.Fore.GREEN + '[COMMAND]' + colorama.Fore.RESET + ' [%(levelname)s] %(message)s')

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
    perform_command_handler.setLevel(perform_command_loglevel)
    perform_command_handler.formatter = perform_command_formatter

    perform_debug_handler = logging.StreamHandler(stream=sys.stdout)
    perform_debug_handler.setLevel(loglevel)
    perform_debug_handler.formatter = perform_debug_formatter

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
        command_logger.setLevel(perform_command_loglevel)
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

logging_config()
