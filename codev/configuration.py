from logging import getLogger

from .deployment import Deployment
from .debug import DebugSettings
from .infrastructure import Infrastructure
from .isolation import Isolation
from .logging import logging_config
from .performer import CommandError

logger = getLogger(__name__)
command_logger = getLogger('command')


class Configuration(object):
    def __init__(self, performer,
                 project_name, environment_name, name, settings,
                 source, next_source=None, disable_isolation=False):
        self.name = name
        self.project_name = project_name
        self.environment_name = environment_name
        self.settings = settings
        self.performer = performer
        self.source = source
        self.next_source = next_source
        self.isolation = None

        if disable_isolation:
            if next_source:
                raise ValueError('Next source is not allowed with disabled isolation.')
            self.isolation = None
        else:
            self.isolation = Isolation(self.settings.isolation, self.source, self.next_source, self.performer)

        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        self.deployment = Deployment(performer, self.settings.provision)

    def install(self, info):
        if self.isolation:
            info.update(self.info)
            current_source = self.isolation.create(info)
        else:
            current_source = self.source

        version = self.performer.execute('pip3 show codev | grep Version | cut -d " " -f 2')
        logger.info("Run 'codev {version}' in isolation.".format(version=version))

        if DebugSettings.perform_settings:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugSettings.perform_settings.data.items()
                )
            )
        else:
            perform_debug = ''

        logging_config(control_perform=True)
        try:
            installation_options = '-e {environment} -c {configuration} -s {current_source.provider_name}:{current_source.options}'.format(
                current_source=current_source,
                configuration=self.name,
                environment=self.environment_name
            )
            with self.performer.change_directory(current_source.directory):
                self.performer.execute('codev deploy {installation_options} --performer=local --disable-isolation --force {perform_debug}'.format(
                    installation_options=installation_options,
                    perform_debug=perform_debug
                ), logger=command_logger)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            if self.isolation:
                logger.info("Setting up connectivity.")
                self.isolation.connect(self.infrastructure)
            logger.info("Installation has been successfully completed.")
            return True

    def deploy(self, info):
        logger.info("Deploying project.")
        info.update(self.info)
        self.deployment.deploy(self.infrastructure, info)

    def run_script(self, script, arguments=None):
        executor = self.isolation or self.performer

        if arguments is None:
            arguments = {}
        arguments.update(self.info)
        executor.run_script(script, arguments=arguments, logger=command_logger)

    @property
    def info(self):
        """
        Information about configuration (and isolation if exists)
        :return: configuration info
        :rtype: dict
        """
        info = dict(
            source=self.source.name,
            source_options=self.source.options,
            source_ident=self.source.ident,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            next_source_ident=self.next_source.ident if self.next_source else '',
            infrastructure=self.infrastructure.info
        )
        if self.isolation:
            info.update(self.isolation.info)


        # click.echo('Configuration:')
        # for machine_group_name, machines in self.infrastructure'].items():
        #     click.echo('    Machines group: {name}'.format(name=machine_group_name))
        #     for machine in machines:
        #         machine_connectivity = info['connectivity'].get(machine.ident, {})
        #         click.echo('        {machine.ip} {machine.ident}'.format(machine=machine))
        #         for source, target in machine_connectivity.items():
        #             click.echo('                {source} -> {target}'.format(source=source, target=target))
        return info

    def destroy_isolation(self):
        if self.isolation and self.isolation.destroy():
            logger.info('Isolation has been destroyed.')
            return True
        else:
            logger.info('There is no such isolation.')
            return False
