from .debug import DebugSettings

from .infrastructure import Infrastructure
from .isolation import Isolation

from .logging import logging_config
from .performer import CommandError, BaseProxyExecutor
from .provision import Provisioner

from logging import getLogger
logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Provision(BaseProxyExecutor):
    def __init__(self, performer, settings):
        super(Provision, self).__init__(performer)
        self.provisioner = Provisioner(settings.provider, performer, settings_data=settings.specific)
        self.scripts = settings.scripts

    def _onerror(self, arguments, error):
        logger.error(error)
        arguments.update(
            dict(
                command=error.command,
                exit_code=error.exit_code,
                error=error.error
            )
        )
        self.run_scripts(self.scripts.onerror, arguments)

    def deploy(self, infrastructure, deployment_info):
        self.run_scripts(self.scripts.onstart, deployment_info)
        try:
            logger.info('Installing provisioner...')
            self.provisioner.install()

            logger.info('Creating machines...')
            infrastructure.create()

            logger.info('Configuration...')
            self.provisioner.run(infrastructure)
        except CommandError as e:
            self._onerror(deployment_info, e)
            return False
        else:
            try:
                arguments = {}
                arguments.update(deployment_info)
                arguments.update(infrastructure.machines_info())
                self.run_scripts(self.scripts.onsuccess, arguments)
                return True
            except CommandError as e:
                self._onerror(deployment_info, e)
                return False


class Configuration(object):
    def __init__(self, performer, name, settings):
        self.name = name
        self.settings = settings
        self.performer = performer
        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        self.provision = Provision(performer, self.settings.provision)

    def install(self, source, next_source, deployment_info):
        isolation = Isolation(self.settings.isolation, deployment_info, self.performer)
        current_source = isolation.install(source, next_source)

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
            deployment_options = '-e {environment} -c {configuration} -s {current_source.provider_name}:{current_source.options}'.format(
                current_source=current_source,
                configuration=self.name,
                environment=deployment_info['environment']
            )
            with self.performer.change_directory(current_source.directory):
                self.performer.execute('codev deploy {deployment_options} --performer=local --isolator=none --force {perform_debug}'.format(
                    deployment_options=deployment_options,
                    perform_debug=perform_debug
                ), logger=command_logger)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Setting up connectivity.")
            self.performer.connect()
            logger.info("Installation has been successfully completed.")
            return True

    def deploy(self, deployment_info):
        self.provision.deploy(self.infrastructure, deployment_info)
