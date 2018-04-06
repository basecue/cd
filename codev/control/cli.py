from typing import Callable, Optional, Any, Tuple, List

import functools

import click
from colorama import Fore as color, Style as style

from codev import __version__

from codev.core.cli import nice_exception, path_option, bool_exit_enable
from codev.core.utils import parse_options, Status
from codev.core.debug import DebugSettings

from . import CodevControl


def source_transition(codev_control_status: Status) -> str:
    """
    """
    # TODO deploy vs destroy (different highlighted source in transition)
    next_source_available = bool(codev_control_status.isolation.next_source)
    isolation_exists = codev_control_status.isolation.exists

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

        transition = ' -> {color_next_source}{next_source}:{next_source.option}{color_reset}'.format(
            **codev_control_status.isolation, **color_options
        )
    else:
        transition = ''

    return '{color_source}{source.name}:{source.option}{color_reset}{transition}'.format(
        transition=transition,
        **codev_control_status.isolation, **color_options
    )


def confirmation_message(message: str) -> Callable[[Callable], Callable]:
    def decorator(f: Callable) -> Callable:
        @functools.wraps(f)
        def confirmation_wrapper(codev_control: CodevControl, force: bool, **kwargs: Any) -> bool:
            if not force:
                if not click.confirm(
                        message.format(
                            source_transition=source_transition(codev_control.status),
                            configuration=codev_control.status.configuration.name
                        ),
                        **codev_control.status
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


def codev_control_options(func: Callable) -> Callable:
    @functools.wraps(func)
    def codev_control_wrapper(
        configuration: str,
        source: str,
        next_source: str,
        **kwargs: Any
    ) -> bool:
        source_name, source_option = parse_options(source)
        next_source_name, next_source_option = parse_options(next_source)

        codev_control = CodevControl.from_file(
            '.codev',
            configuration_name=configuration,
            source_name=source_name,
            source_option=source_option,
            next_source_name=next_source_name,
            next_source_option=next_source_option
        )
        return func(codev_control, **kwargs)

    f = click.argument(
        'configuration',
        metavar='<cconfiguration>',
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


def debug_option(func: Callable) -> Callable:
    @functools.wraps(func)
    def debug_wrapper(debug: List[Tuple[str, str]], debug_perform: List[Tuple[str, str]], **kwargs: Any) -> bool:
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


def command(
    confirmation: Optional[str] = None,
    bool_exit: bool = True,
    **kwargs: Any
) -> Callable[[Callable], Callable]:
    def decorator(func: Callable) -> Callable:
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


@click.group(invoke_without_command=True)
@click.option('--version', is_flag=True, help="Show version number and exit.")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    if version:
        click.echo(__version__)
    elif not ctx.invoked_subcommand:
        click.echo(ctx.get_help())
