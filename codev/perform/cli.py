import click
from functools import wraps

from codev.core.cli import configuration_with_option, nice_exception, path_option, bool_exit_enable, main

from codev.core.utils import parse_options
from codev.core.debug import DebugSettings

from . import CodevPerform


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(codev_perform, force, **kwargs):
            if not force:
                codev_perform_status = codev_perform.status
                if not click.confirm(
                    message.format(
                        configuration_with_option=configuration_with_option(
                            codev_perform_status['configuration'], codev_perform_status['configuration_name']
                        ),
                        **codev_perform_status,
                    )
                ):
                    raise click.Abort()
            return f(codev_perform, **kwargs)

        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help='Force to run the command. Avoid the confirmation.'
        )(confirmation_wrapper)

    return decorator


def codev_perform_options(func):
    @wraps(func)
    def codev_perform_wrapper(
            settings,
            configuration,
            **kwargs):

        configuration_name, configuration_option = parse_options(configuration)

        codev_perform = CodevPerform(
            settings,
            configuration_name,
            configuration_option=configuration_option,
        )
        return func(codev_perform, **kwargs)

    return click.argument(
        'configuration',
        metavar='<configuration:option>',
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


def command(confirmation=None, bool_exit=True, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = codev_perform_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
