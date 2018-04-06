from typing import Callable, Any

import functools
import logging
import os
import sys

import click

from .debug import DebugSettings

logger = logging.getLogger(__name__)


def nice_exception(func: Callable) -> Callable:
    @functools.wraps(func)
    def nice_exception_wrapper(*args: Any, **kwargs: Any) -> bool:
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


def path_option(func: Callable) -> Callable:
    @functools.wraps(func)
    def path_wrapper(path: str, *args: Any, **kwargs: Any) -> bool:
        os.chdir(path)
        return func(*args, **kwargs)

    return click.option('-p', '--path',
                        default='./',
                        metavar='<path to repository>',
                        help='path to repository')(path_wrapper)


def bool_exit_enable(func: Callable) -> Callable:
    @functools.wraps(func)
    def bool_exit(*args: Any, **kwargs: Any) -> None:
        value = func(*args, **kwargs)
        if value:
            sys.exit(0)
        else:
            sys.exit(1)

    return bool_exit
