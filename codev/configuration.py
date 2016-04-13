from colorama import Fore as color, Style as style
from logging import getLogger

from .debug import DebugSettings

from .infrastructure import Infrastructure
from .isolation import Isolation

from .logging import logging_config
from .performer import CommandError, BaseProxyExecutor
from .provision import Provisioner


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
    def __init__(self, performer, project_name, environment_name, name, settings, source, next_source):
        self.name = name
        self.project_name = project_name
        self.environment_name = environment_name
        self.settings = settings
        self.performer = performer
        self.source = source
        self.next_source = next_source
        self.infrastructure = Infrastructure(performer, self.settings.infrastructure)
        self.provision = Provision(performer, self.settings.provision)

    def install(self):
        isolation = Isolation(self.settings.isolation, self.deployment_info(colorize=False), self.performer)
        current_source = isolation.create(self.source, self.next_source)

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
                environment=self.deployment_info()['environment']
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

    def deploy(self):
        logger.info("Deploying project.")
        self.provision.deploy(self.infrastructure, self.deployment_info(colorize=False))

    def run_script(self, script, arguments=None):
        isolation = Isolation(self.settings.isolation, self.deployment_info(), self.performer)

        if arguments is None:
            arguments = {}
        arguments.update(self.deployment_info(colorize=False))
        with isolation.change_directory(self.current_source.directory):
            isolation.run_script(script, arguments=arguments, logger=command_logger)

    @property
    def current_source(self):
        # isolator
        if self.next_source and self.performer.exists():
            return self.next_source
        else:
            return self.source

    def source_transition(self, colorize=True):
        deployment_info = self.deployment_info(transition=False)

        if colorize:
            color_options = dict(
                color_source=color.GREEN,
                color_reset=color.RESET + style.RESET_ALL
            )
        else:
            color_options = dict(
                color_source='',
                color_reset='',
                color_next_source='',
            )

        if self.next_source:
            if colorize:
                if not self.current_source:
                    color_source = color.GREEN
                    color_next_source = color.GREEN
                elif self.current_source == self.source:
                    color_source = color.GREEN + style.BRIGHT
                    color_next_source = color.GREEN
                else:
                    color_source = color.GREEN
                    color_next_source = color.GREEN + style.BRIGHT

                color_options.update(dict(
                    color_source=color_source,
                    color_next_source=color_next_source,
                ))

            deployment_info.update(color_options)
            transition = ' -> {color_next_source}{next_source}:{next_source_options}{color_reset}'.format(
                **deployment_info
            )
        else:
            transition = ''

        deployment_info.update(color_options)
        return '{color_source}{source}:{source_options}{color_reset}{transition}'.format(
            transition=transition,
            **deployment_info
        )

    def deployment_info(self, transition=True, colorize=True):
        return dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.name,
            source=self.source.name,
            source_options=self.source.options,
            next_source=self.next_source.name if self.next_source else '',
            next_source_options=self.next_source.options if self.next_source else '',
            source_transition=self.source_transition(colorize) if transition else ''
        )