import click
from colorama import Fore as color, Style as style
from functools import wraps

from codev_core import __version__
from codev_core.utils import parse_options
from codev_core.settings import YAMLSettingsReader
from codev_core.debug import DebugSettings
from codev_core.logging import logging_config

from .installation import Installation

from os import chdir
import sys


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(installation, force, **kwargs):
            if not force:
                installation_status = installation.status
                if not click.confirm(
                        message.format(
                            **installation_status
                        )
                ):
                    raise click.Abort()
            return f(installation, **kwargs)

        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help='Force to run the command. Avoid the confirmation.'
        )(confirmation_wrapper)

    return decorator


def basic_options(func):
    @wraps(func)
    def installation_wrapper(
            settings,
            environment_configuration,
            **kwargs):

        environment, configuration = parse_options(environment_configuration)

        installation = Installation(
            settings,
            environment,
            configuration_name=configuration,
        )
        return func(installation, **kwargs)

    return click.argument(
        'environment_configuration',
        metavar='<environment:configuration>',
        required=True)(installation_wrapper)


def nice_exception(func):
    @wraps(func)
    def nice_exception_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if DebugSettings.settings.show_client_exception:
                raise
            if issubclass(type(e), click.ClickException) or issubclass(type(e), RuntimeError):
                raise
            raise click.ClickException(e)
    return nice_exception_wrapper


def path_option(func):
    @wraps(func)
    def settings_wrapper(path, *args, **kwargs):
        chdir(path)
        settings = YAMLSettingsReader().from_file('.codev')
        return func(settings, *args, **kwargs)

    return click.option('-p', '--path',
                        default='./',
                        metavar='<path to repository>',
                        help='path to repository')(settings_wrapper)


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, debug_perform, **kwargs):
        if debug:
            DebugSettings.settings = DebugSettings(dict(debug))
            logging_config(DebugSettings.settings.loglevel)

        if debug_perform:
            DebugSettings.perform_settings = DebugSettings(dict(debug_perform))

        return func(**kwargs)

    return click.option(
        '--debug',
        type=click.Tuple([str, str]),
        multiple=True,
        metavar='<variable> <value>',
        help='Debug options.'
    )(debug_wrapper)


def bool_exit_enable(func):
    @wraps(func)
    def bool_exit(*args, **kwargs):
        value = func(*args, **kwargs)
        if value:
            sys.exit(0)
        else:
            sys.exit(1)

    return bool_exit


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True,  help="Show version number and exit.")
@click.pass_context
def main(ctx, version):
    if version:
        click.echo(__version__)
    elif not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


def command(confirmation=None, bool_exit=True, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = basic_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
