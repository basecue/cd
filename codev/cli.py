from functools import wraps
from os import chdir
import sys

import click
from colorama import Fore as color, Style as style

from codev_core import __version__
from codev_core.utils import parse_options
from codev_core.settings import YAMLSettingsReader
from codev_core.debug import DebugSettings
from codev_core.log import logging_config

from .installation import Installation


def source_transition(installation_status):
    """
    :param installation_status:
    :return:
    """
    # TODO deploy vs destroy (different highlited source in transition)
    next_source_available = bool(installation_status['next_source_ident'])
    isolation_exists = 'ident' in installation_status.get('isolation', {})

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

        final = {}
        final.update(installation_status)
        final.update(color_options)
        # TODO in python 3.5 use **installation_status, **color_options
        transition = ' -> {color_next_source}{next_source}:{next_source_options}{color_reset}'.format(
            **final
        )
    else:
        transition = ''

    final2 = {}
    final2.update(installation_status)
    final2.update(color_options)
    # TODO in python 3.5 use **installation_status, **color_options
    return '{color_source}{source}:{source_options}{color_reset}{transition}'.format(
        transition=transition,
        **final2
    )


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(installation, force, **kwargs):
            if not force:
                installation_status = installation.status
                if not click.confirm(
                        message.format(
                            source_transition=source_transition(installation_status),
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


def installation_options(func):
    @wraps(func)
    def installation_wrapper(
            settings,
            environment_configuration,
            source,
            next_source,
            same_source,
            **kwargs):

        if same_source:
            if source or next_source:
                raise click.BadOptionUsage('Parameter "-st" is not allowed to use together with "-s" / "--source" or "-t" / "--next-source" parameters.')
            else:
                source = next_source = same_source
        # elif not source:
        #     raise click.BadOptionUsage('Missing option "-s" / "--source" or "-st"')

        source_name, source_options = parse_options(source)
        next_source_name, next_source_options = parse_options(next_source)
        environment, configuration = parse_options(environment_configuration)

        installation = Installation(
            settings,
            environment,
            configuration_name=configuration,
            source_name=source_name,
            source_options=source_options,
            next_source_name=next_source_name,
            next_source_options=next_source_options
        )
        return func(installation, **kwargs)

    f = click.argument(
        'environment_configuration',
        metavar='<environment:configuration>',
        required=True)(installation_wrapper)

    f = click.option(
        '-s', '--source',
        metavar='<source installation>',
        help='Source')(f)

    f = click.option(
        '-t', '--next-source',
        default='',
        metavar='<next source>',
        help='Next source')(f)

    return click.option(
        '-st', 'same_source',
        default='',
        metavar='<source>',
        help='Shortcut for same source and next source')(f)


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
        func = installation_options(func)
        func = nice_exception(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
