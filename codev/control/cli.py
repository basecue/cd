import sys

import click
from colorama import Fore as color, Style as style
from functools import wraps
from os import chdir

from codev import __version__
from codev.core.cli import configuration_with_option
from codev.core.settings import YAMLSettingsReader
from codev.core.utils import parse_options
from codev.core.debug import DebugSettings

from . import CodevControl


def source_transition(codev_control_status):
    """
    :param installation_status:
    :return:
    """
    # TODO deploy vs destroy (different highlighted source in transition)
    next_source_available = bool(codev_control_status['next_source_ident'])
    isolation_exists = 'ident' in codev_control_status.get('isolation', {})

    color_options = dict(
        color_source=color.GREEN,
        color_reset=color.RESET + style.RESET_ALL
    )

    if next_source_available:
        if not isolation_exists:
            color_source = color.GREEN + style.BRIGHT
            color_next_source = color.GREEN
        else:
            color_source = color.GREEN
            color_next_source = color.GREEN + style.BRIGHT

        color_options.update(dict(
            color_source=color_source,
            color_next_source=color_next_source,
        ))

        transition = ' -> {color_next_source}{next_source}:{next_source_options}{color_reset}'.format(
            **codev_control_status, **color_options
        )
    else:
        transition = ''

    return '{color_source}{source}:{source_options}{color_reset}{transition}'.format(
        transition=transition,
        **codev_control_status, **color_options
    )


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(codev_control, force, **kwargs):
            if not force:
                codev_control_status = codev_control.status
                if not click.confirm(
                        message.format(
                            source_transition=source_transition(codev_control_status),
                            configuration_with_option=configuration_with_option(
                                codev_control_status['configuration'], codev_control_status['configuration_option']
                            ),
                            **codev_control_status
                        )
                ):
                    raise click.Abort()
            return f(codev_control, **kwargs)

        return click.option(
            '-f',
            '--force',
            is_flag=True,
            help='Force to run the command. Avoid the confirmation.'
        )(confirmation_wrapper)

    return decorator


def codev_control_options(func):
    @wraps(func)
    def codev_control_wrapper(
            settings,
            configuration,
            source,
            next_source,
            **kwargs):

        source_name, source_options = parse_options(source)
        next_source_name, next_source_options = parse_options(next_source)
        configuration_name, configuration_option = parse_options(configuration)

        codev_control = CodevControl(
            settings,
            configuration_name,
            configuration_option=configuration_option,
            source_name=source_name,
            source_options=source_options,
            next_source_name=next_source_name,
            next_source_options=next_source_options
        )
        return func(codev_control, **kwargs)

    f = click.argument(
        'configuration',
        metavar='<configuration:option>',
        required=True)(codev_control_wrapper)

    f = click.option(
        '-s', '--source',
        default='',
        metavar='<source>',
        help='Source')(f)

    return click.option(
        '-t', '--next-source',
        default='',
        metavar='<next source>',
        help='Next source')(f)


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

        if debug_perform:
            DebugSettings.perform_settings = DebugSettings(dict(debug_perform))

        return func(**kwargs)

    f = click.option(
        '--debug-perform',
        type=click.Tuple([str, str]),
        multiple=True,
        metavar='<variable> <value>',
        help='Debug perform options.'
    )

    return f(
        click.option(
            '--debug',
            type=click.Tuple([str, str]),
            multiple=True,
            metavar='<variable> <value>',
            help='Debug options.'
        )(debug_wrapper)
    )


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
        func = codev_control_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
