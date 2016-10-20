import click
from colorama import Fore as color, Style as style
from functools import wraps

from .settings import YAMLSettingsReader
from .installation import Installation
from .debug import DebugSettings
from .logging import logging_config
from .info import VERSION
from os import chdir
import sys


def source_transition(installation_info):
    """
    :param installation_info:
    :return:
    """
    # TODO deploy vs destroy (different highlited source in transition)
    next_source_available = bool(installation_info['next_source_ident'])
    isolation_exists = 'ident' in installation_info.get('isolation', {})

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
        final.update(installation_info)
        final.update(color_options)
        # TODO in python 3.5 use **installation_info, **color_options
        transition = ' -> {color_next_source}{next_source}:{next_source_options}{color_reset}'.format(
            **final
        )
    else:
        transition = ''

    final2 = {}
    final2.update(installation_info)
    final2.update(color_options)
    # TODO in python 3.5 use **installation_info, **color_options
    return '{color_source}{source}:{source_options}{color_reset}{transition}'.format(
        transition=transition,
        **final2
    )


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(installation, force, **kwargs):
            if not force:
                installation_info = installation.info
                if not click.confirm(
                        message.format(
                            source_transition=source_transition(installation_info),
                            **installation_info
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


def parse_source(inp):
    parsed = inp.split(':', 1)
    name = parsed[0]
    options = parsed[1] if len(parsed) == 2 else ''
    return name, options


def installation_options(func):
    @wraps(func)
    def installation_wrapper(
            settings,
            environment,
            configuration,
            source,
            next_source,
            same_source,
            performer,
            performer_settings_data,
            disable_isolation, **kwargs):

        if same_source:
            if source or next_source:
                raise click.BadOptionUsage('Parameter "-st" is not allowed to use together with "-s" / "--source" or "-t" / "--next-source" parameters.')
            else:
                source = next_source = same_source
        elif not source:
            raise click.BadOptionUsage('Missing option "-s" / "--source" or "-st"')

        source_name, source_options = parse_source(source)
        next_source_name, next_source_options = parse_source(next_source)

        installation = Installation(
            settings,
            environment,
            configuration,
            source_name,
            source_options,
            next_source_name=next_source_name,
            next_source_options=next_source_options,
            performer_provider=performer,
            performer_settings_data=performer_settings_data,
            disable_isolation=disable_isolation
        )
        return func(installation, **kwargs)

    f = click.option(
        '-e', '--environment',
        metavar='<environment>',
        required=True,
        help='environment')(installation_wrapper)

    f = click.option(
        '-c', '--configuration',
        metavar='<configuration>',
        required=True,
        help='configuration')(f)

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


def performer_option(func):
    return click.option('--performer',
                        default=None,
                        metavar='<performer>',
                        help='Set performer')(func)


def performer_settings_option(func):
    @wraps(func)
    def performer_settings_wrapper(*args, performer_settings, **kwargs):
        return func(*args, performer_settings_data=dict(performer_settings), **kwargs)

    return click.option('--performer-settings',
                        type=click.Tuple([str, str]),
                        multiple=True,
                        metavar='<variable> <value>',
                        help='Performer settings.')(performer_settings_wrapper)


def disable_isolation_option(func):
    return click.option('--disable-isolation',
                        is_flag=True,
                        default=False,
                        help='Disable isolation')(func)


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
        click.echo(VERSION)
    elif not ctx.invoked_subcommand:
        click.echo(ctx.get_help())


def command(confirmation=None, bool_exit=True, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = installation_options(func)
        func = nice_exception(func)
        func = performer_option(func)
        func = performer_settings_option(func)
        func = disable_isolation_option(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
