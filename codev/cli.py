# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import click
from functools import wraps
from git import Repo

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
            logging_config(
                perform=True,
                perform_command_loglevel=DebugConfiguration.configuration.perform_command_loglevel
            )
            if not DebugConfiguration.configuration.disable_version_check:
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

        repository_dir = DebugConfiguration.configuration.repository_dir or repo.working_dir
        configuration_dir = DebugConfiguration.configuration.configuration_dir or repo.working_dir
        repository_url = DebugConfiguration.configuration.repository_url or repo.remotes.origin.url
        configuration = YAMLConfigurationReader().from_file('%s/.codev' % configuration_dir, repository_url=repository_url)

        chdir(repository_dir)
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


@click.group()
def main():
    pass


def command(confirmation=None, perform=False, bool_exit=True, **kwargs):
    def decorator(func):
        if confirmation:
            func = confirmation_message(confirmation)(func)
        func = deployment_option(func)
        func = nice_exception(func)
        if perform:
            func = perform_option(func)
        func = path_option(func)
        func = debug_option(func)
        if bool_exit:
            func = bool_exit_enable(func)
        func = main.command(**kwargs)(func)
        return func
    return decorator
