import sys
from functools import wraps
from logging import getLogger
from os import chdir

import click

from .debug import DebugSettings

logger = getLogger(__name__)



def nice_exception(func):
    @wraps(func)
    def nice_exception_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if DebugSettings.settings.show_exception:
                raise
            if issubclass(type(e), click.ClickException) or issubclass(type(e), RuntimeError):
                raise
            # TODO log traceback to some logfile
            logger.error(e)
            return False
    return nice_exception_wrapper


def path_option(func):
    @wraps(func)
    def path_wrapper(path, *args, **kwargs):
        chdir(path)
        return func(*args, **kwargs)

    return click.option('-p', '--path',
                        default='./',
                        metavar='<path to repository>',
                        help='path to repository')(path_wrapper)


def bool_exit_enable(func):
    @wraps(func)
    def bool_exit(*args, **kwargs):
        value = func(*args, **kwargs)
        if value:
            sys.exit(0)
        else:
            sys.exit(1)

    return bool_exit
