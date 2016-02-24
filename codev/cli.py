import click
from functools import wraps
from git import Repo

from .configuration import YAMLConfigurationReader
from .deployment import Deployment
from .debug import DebugConfiguration
from .logging import logging_config
from .info import VERSION
from os import chdir


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(deployment, force, **kwargs):
            if not force:
                if not click.confirm(message.format(deployment=deployment)):
                    raise click.Abort()
            return f(deployment, **kwargs)

        return click.option('-f', '--force', is_flag=True,  help='Force to run the command. Avoid the confirmation.')(confirmation_wrapper)

    return decorator


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
        return func(deployment, **kwargs)

    return click.option('-d', '--deployment',
                        metavar='<deployment identification>',
                        required=True,
                        nargs=3,
                        help='environment infrastructure installation')(deployment_wrapper)


def perform_option(func):
    @wraps(func)
    def perform_wrapper(configuration, *args, **kwargs):
        perform = kwargs.get('perform')
        if perform:
            logging_config(perform=True)
            # if DebugConfiguration.configuration.perform_command_output:
            #     command_logger.set_perform_debug_command_output()
        assert configuration.version == VERSION
        return func(configuration, *args, **kwargs)

    return click.option('--perform',
                        is_flag=True,
                        help='Enable perform mode')(perform_wrapper)


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
        repo = Repo(search_parent_directories=True)
        directory = DebugConfiguration.configuration.directory or repo.working_dir
        repository_url = DebugConfiguration.configuration.repository or repo.remotes.origin.url
        configuration = YAMLConfigurationReader().from_file('%s/.codev' % directory, repository_url=repository_url)
        return func(configuration, *args, **kwargs)

    return click.option('-p', '--path',
                        default='./',
                        metavar='<path to repository>',
                        help='path to repository')(configuration_wrapper)


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, *args, **kwargs):
        if debug:
            DebugConfiguration.configuration = YAMLConfigurationReader(DebugConfiguration).from_file(debug)
            logging_config(DebugConfiguration.configuration.loglevel)

        return func(*args, **kwargs)

    return click.option('--debug',
                        metavar='<debug file name>',
                        default=None,
                        help='Path to debug configuration file.')(debug_wrapper)


@click.group()
def main():
    pass


def command(confirmation=None, perform=False, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = deployment_option(func)
        func = nice_exception(func)
        if perform:
            func = perform_option(func)
        func = path_option(func)
        func = debug_option(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
