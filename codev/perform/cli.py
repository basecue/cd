import click
from functools import wraps

from codev import __version__

from codev.core.cli import nice_exception, path_option, bool_exit_enable

from codev.core.debug import DebugSettings

from . import CodevPerform


def codev_perform_options(func):
    @wraps(func)
    def codev_perform_wrapper(
            configuration,
            **kwargs):

        codev_perform = CodevPerform.from_file(
            '.codev',
            configuration_name=configuration,
        )
        return func(codev_perform, **kwargs)

    return click.argument(
        'configuration',
        metavar='<configuration>',
        required=True)(codev_perform_wrapper)


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, **kwargs):
        if debug:
            DebugSettings.settings = DebugSettings(dict(debug))

        return func(**kwargs)

    return click.option(
        '--debug',
        type=click.Tuple([str, str]),
        multiple=True,
        metavar='<variable> <value>',
        help='Debug options.'
    )(debug_wrapper)


def version_option(func):
    @wraps(func)
    def version_wrapper(version, **kwargs):
        if version:
            click.echo(__version__)

        return func(**kwargs)

    return click.option(
        '--version',
        is_flag=True,
        help="Show version number and exit."
    )(version_wrapper)


def command(bool_exit=True, **kwargs):
    def decorator(func):
        func = codev_perform_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        func = version_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = click.command()(func)
        return func
    return decorator


