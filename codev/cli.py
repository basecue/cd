import click
from functools import wraps

from .configuration import YAMLConfigurationReader
from .deployment import Deployment
from .debug import DebugConfiguration
from .logging import logging_config
from .info import VERSION
from os import chdir
import sys


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(deployment, force, **kwargs):
            if not force:
                if not click.confirm(message.format(**deployment.deployment_info())):
                    raise click.Abort()
            return f(deployment, **kwargs)

        return click.option('-f', '--force', is_flag=True,  help='Force to run the command. Avoid the confirmation.')(confirmation_wrapper)

    return decorator


def parse_installation(inp):
    parsed = inp.split(':', 1)
    name = parsed[0]
    options = parsed[1] if len(parsed) == 2 else ''
    return name, options


def deployment_options(func):
    @wraps(func)
    def deployment_wrapper(
            configuration,
            environment,
            infrastructure,
            installation,
            next_installation,
            performer,
            disable_isolation, **kwargs):
        installation_name, installation_options = parse_installation(installation)
        next_installation_name, next_installation_options = parse_installation(next_installation)

        deployment = Deployment(
            configuration,
            environment,
            infrastructure,
            installation_name,
            installation_options,
            next_installation_name=next_installation_name,
            next_installation_options=next_installation_options,
            performer_provider=performer,
            performer_specific={},  # TODO
            disable_isolation=disable_isolation
        )
        return func(deployment, **kwargs)

    f = click.option(
        '-e', '--environment',
        metavar='<environment>',
        required=True,
        help='environment')(deployment_wrapper)

    f = click.option(
        '-i', '--infrastructure',
        metavar='<infrastructure>',
        required=True,
        help='infrastructure')(f)

    f = click.option(
        '-s', '--installation',
        metavar='<source installation>',
        required=True,
        help='Source installation')(f)

    return click.option(
        '-n', '--next-installation',
        default='',
        metavar='<next installation>',
        help='Next installation')(f)


def performer_option(func):
    return click.option('--performer',
                        default=None,
                        metavar='<performer>',
                        help='Set performer')(func)


def isolation_option(func):
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
            if DebugConfiguration.configuration.show_client_exception:
                raise
            if issubclass(type(e), click.ClickException) or issubclass(type(e), RuntimeError):
                raise
            raise click.ClickException(e)
    return nice_exception_wrapper


def path_option(func):
    @wraps(func)
    def configuration_wrapper(path, *args, **kwargs):
        chdir(path)
        configuration = YAMLConfigurationReader().from_file('.codev')
        return func(configuration, *args, **kwargs)

    return click.option('-p', '--path',
                        default='./',
                        metavar='<path to repository>',
                        help='path to repository')(configuration_wrapper)


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, debug_perform, **kwargs):
        if debug:
            DebugConfiguration.configuration = DebugConfiguration(dict(debug))
            logging_config(DebugConfiguration.configuration.loglevel)

        if debug_perform:
            DebugConfiguration.perform_configuration = DebugConfiguration(dict(debug_perform))

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
        func = deployment_options(func)
        func = nice_exception(func)
        func = performer_option(func)
        func = isolation_option(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
