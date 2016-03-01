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
#     51 Franklin Street, Fifth Floor, Boston, MA 0<110-1301 USA.

from .environment import Environment
from .installation import Installation
from .debug import DebugConfiguration
from .logging import logging_config
from .performer import CommandError
from .configuration import YAMLConfigurationReader
from colorama import Fore as color

from logging import getLogger

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Deployment(object):
    """
    Represents deployment of project. It's basic starting point for all commands.
    """
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name, installation_options):
        environment_configuration = configuration.environments[environment_name]
        installation_configuration = environment_configuration.installations[installation_name]

        self._installation = Installation(
            installation_name,
            installation_options,
            configuration_data=installation_configuration
        )

        self.ident = '%s_%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name,
            self._installation.ident
        )
        self._environment = Environment(environment_configuration, infrastructure_name, self.ident)

        self.project_name = configuration.project
        self.environment_name, self.infrastructure_name, self.installation_name, self.installation_options = \
            environment_name, infrastructure_name, installation_name, installation_options

    def _isolation(self, create=False):
        if create:
            logger.info("Creating isolation...")
            self._environment.isolation.create()
        logger.info("Entering isolation...")
        return self._environment.isolation

    def install(self):
        """
        Create isolation if it does not exist and start installation in isolation.

        :return: True if installation is sucessfully realized
        :rtype: bool
        """
        logger.info("Starting installation...")
        isolation = self._isolation(create=True)

        logger.info("Install project to isolation.")
        directory = self._installation.install(isolation)

        with isolation.get_fo('{directory}/.codev'.format(directory=directory)) as codev_file:
            version = YAMLConfigurationReader().from_yaml(codev_file).version

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if not DebugConfiguration.configuration.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugConfiguration.configuration.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
            isolation.send_file(distfile, '/tmp/codev.tar.gz')
            isolation.execute('pip3 install --upgrade /tmp/codev.tar.gz')

        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        if DebugConfiguration.perform_configuration:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugConfiguration.perform_configuration.data.items()
                )
            )
        else:
            perform_debug = ''

        logging_config(control_perform=True)
        try:
            isolation.background_execute('codev install -d {environment_name} {infrastructure_name} {installation_name}:{installation_options} --path {directory} --perform --force {perform_debug}'.format(
                environment_name=self.environment_name,
                infrastructure_name=self.infrastructure_name,
                installation_name=self.installation_name,
                installation_options=self.installation_options,
                directory=directory,
                perform_debug=perform_debug
            ), logger=command_logger)
        except CommandError as e:
            logger.debug(e)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Installation has been successfully completed.")
            return True

    def provision(self):
        """
        Run provisions

        :return: True if provision succesfully proceeds
        :rtype: bool
        """
        try:
            return self._environment.provision()
        except CommandError as e:
            logger.error(e)
            return False

    def execute(self, command):
        """
        Create isolation if it does not exist and execute command in isolation.


        :param command: Command to execute
        :type command: str
        :return: True if executed command returns 0
        :rtype: bool
        """
        isolation = self._isolation(create=True)

        logging_config(control_perform=True)
        try:
            isolation.background_execute(command, logger=command_logger)
        except CommandError as e:
            logger.error(e)
            return False
        else:
            logger.info('Command finished.')
            return True

    def join(self):
        """
        Stop the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        logging_config(control_perform=True)
        isolation = self._isolation()
        if isolation.background_join(logger=command_logger):
            logger.info('Command finished.')
            return True
        else:
            logger.error('No running command.')
            return False

    def stop(self):
        """
        Stop the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        isolation = self._isolation()
        if isolation.background_stop():
            logger.info('Stop signal has been sent.')
            return True
        else:
            logger.error('No running command.')
            return False

    def kill(self):
        """
        Kill the running command in isolation

        :return: True if command was running
        :rtype: bool
        """
        isolation = self._isolation()
        if isolation.background_kill():
            logger.info('Command has been killed.')
            return True
        else:
            logger.error('No running command.')
            return False

    def shell(self):
        """
        Create isolation if it does not exist and invoke 'shell' in isolation.

        :return:
        :rtype: bool
        """
        isolation = self._isolation(create=True)
        logger.info('Entering isolation shell.')

        #support for history
        import readline
        shell_logger = getLogger('shell')
        SEND_FILE_SHELL_COMMAND = 'send'

        while True:
            command = input(
                (color.GREEN +
                 '{project_name} {environment_name} {infrastructure_name} {installation_name}:{installation_options}' +
                 color.RESET + ':' + color.BLUE + '~' + color.RESET + '$ ').format(
                    project_name=self.project_name,
                    environment_name=self.environment_name,
                    infrastructure_name=self.infrastructure_name,
                    installation_name=self.installation_name,
                    installation_options=self.installation_options
                )
            )
            if command in ('exit', 'quit', 'logout'):
                return True
            if command.startswith(SEND_FILE_SHELL_COMMAND):
                try:
                    source, target = command[len(SEND_FILE_SHELL_COMMAND):].split()
                except ValueError:
                    shell_logger.error('Command {command} needs exactly two arguments: <source> and <target>.'.format(
                        command=SEND_FILE_SHELL_COMMAND
                    ))
                else:
                    try:
                        isolation.send_file(source, target)
                    except CommandError as e:
                        shell_logger.error(e.error)
                continue
            try:
                isolation.background_execute(command, logger=shell_logger)
            except CommandError as e:
                shell_logger.error(e.error)

    def run(self, script):
        """
        Create isolation if it does not exist and run script in isolation.

        :param script: Name of the script
        :type param: str
        :return:
        :rtype: bool
        """
        # TODO
        pass

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation
        :rtype: bool
        """
        isolation = self._isolation()
        return isolation.destroy()
