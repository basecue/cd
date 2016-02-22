import click
from functools import wraps

from .configuration import YAMLConfigurationReader
from .deployment import Deployment
from .debug import DebugConfiguration
from .logging import control_logging, perform_logging, command_logger
from .info import VERSION


def configuration_option(func):
    @wraps(func)
    def configuration_wrapper(configuration, *args, **kwargs):
        return func(*args, **kwargs)

    def callback(ctx, param, value):
        configuration = YAMLConfigurationReader().from_file(value)
        return configuration

    return click.option('-c', '--configuration',
                        default='.codev',
                        help='Path to configuration file.',
                        callback=callback)(configuration_wrapper)


def deployment_option(func):
    @wraps(func)
    def deployment_wrapper(configuration, deployment, **kwargs):
        environment_name = deployment[0]
        infrastructure_name = deployment[1]
        installation = deployment[2]

        parsed_installation = installation.split(':', 1)
        installation_name = parsed_installation[0]
        installation_options = parsed_installation[1] if len(parsed_installation) == 2 else ''
        deployment = Deployment(
            configuration, environment_name, infrastructure_name, installation_name, installation_options
        )
        return func(configuration, deployment, **kwargs)

    return click.option('-d', '--deployment',
                        required=True,
                        nargs=3,
                        help='environment infrastructure installation')(deployment_wrapper)


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(configuration, deployment, force, **kwargs):
            if not force:
                if not click.confirm(message.format(configuration=configuration, deployment=deployment)):
                    raise click.Abort()
            return f(configuration, deployment, **kwargs)

        return click.option('-f', '--force', is_flag=True,  help='Force')(confirmation_wrapper)

    return decorator


def perform_option(func):
    @wraps(func)
    def perform_wrapper(configuration, *args, **kwargs):
        perform_logging(DebugConfiguration.configuration.loglevel)
        if DebugConfiguration.configuration.perform_command_output:
            command_logger.set_perform_command_output()
        assert configuration.version == VERSION
        return func(configuration, *args, **kwargs)

    return click.option('--perform',
                        is_flag=True,
                        help='Perform mode')(perform_wrapper)


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


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, *args, **kwargs):
        if debug:
            DebugConfiguration.configuration = YAMLConfigurationReader(DebugConfiguration).from_file(debug)
        control_logging(DebugConfiguration.configuration.loglevel)
        return func(*args, **kwargs)

    return click.option('--debug',
                        default=None,
                        help='Path to debug configuration file.')(debug_wrapper)


@click.group()
def main():
    pass


def command(confirmation=None, perform=False):
    def decorator(func):
        func = configuration_option(func)
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = deployment_option(func)
        func = nice_exception(func)
        if perform:
            func = perform_option(func)
        func = debug_option(func)
        func = main.command()(func)
        return func
    return decorator
