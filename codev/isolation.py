from logging import getLogger
from json import dumps

from .performer import ScriptExecutor
from .logging import logging_config
from .performer import CommandError
from .debug import DebugSettings
from .settings import YAMLSettingsReader

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Isolation(ScriptExecutor):
    def __init__(self, settings, source, next_source, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = self.performer
        self.settings = settings
        self.source = source
        self.next_source = next_source
        self.current_source = self.next_source if self.next_source and self.exists() else self.source

    def connect(self, infrastructure):
        """
        :param isolation:
        :return:
        """
        for machine_ident, connectivity_conf in self.settings.connectivity.items():
            machine = infrastructure.get_machine_by_ident(machine_ident)

            for source_port, target_port in connectivity_conf.items():
                self.isolator.redirect(machine.ip, source_port, target_port)

    def _install_codev(self, codev_file):
        version = YAMLSettingsReader().from_yaml(codev_file).version
        self.execute('pip3 install setuptools')

        # uninstall previous version of codev (ignore if not installed)
        self.check_execute('pip3 uninstall codev -y')

        # install proper version of codev
        # TODO requirements - 'python3-pip', 'libffi-dev', 'libssl-dev'
        if not DebugSettings.settings.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            self.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugSettings.settings.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))

            from os.path import basename
            remote_distfile = '/tmp/{distfile}'.format(distfile=basename(distfile))

            self.send_file(distfile, remote_distfile)
            self.execute('pip3 install --upgrade {distfile}'.format(distfile=remote_distfile))

    def execute_script(self, script, arguments=None, logger=None):
        if DebugSettings.perform_settings:
            perform_debug = ' '.join(
                (
                    '--debug {key} {value}'.format(key=key, value=value)
                    for key, value in DebugSettings.perform_settings.data.items()
                )
            )
        else:
            perform_debug = ''
        arguments.update(self.info)
        codev_script = 'codev execute {environment}:{configuration} -s {source}:{source_options} --performer=local --disable-isolation {perform_debug} -- {script}'.format(
            script=script,
            environment=arguments['environment'],
            configuration=arguments['configuration'],
            source=arguments['source'],
            source_options=arguments['source_options'],
            perform_debug=perform_debug
        )
        with self.change_directory(self.current_source.directory):
            super().execute_script(codev_script, arguments=arguments, logger=logger)

    def _install_project(self):
        self.current_source.install(self.performer)

        # load .codev file from source and install codev with specific version
        with self.current_source.open_codev_file(self.performer) as codev_file:
            self._install_codev(codev_file)

    def install(self, info):
        # TODO refactorize - divide?
        if not self.isolator.exists():
            logger.info("Creating isolation...")
            self.isolator.create()
            created = True
        else:
            if not self.isolator.is_started():
                self.isolator.start()
            created = False

        self.current_source = self.source
        if created:
            logger.info("Install project to isolation...")
            self._install_project()
            self.execute_scripts(self.settings.scripts.oncreate, info, logger=command_logger)
        else:
            if self.next_source:
                logger.info("Transition source in isolation...")
                self.current_source = self.next_source
                self._install_project()
        logger.info("Entering isolation...")
        self.execute_scripts(self.settings.scripts.onenter, info, logger=command_logger)

    def deploy(self, infrastructure, info, vars):
        # TODO python3.5
        # deploy_vars = {**self.settings.vars, **vars}
        deploy_vars = self.settings.vars.copy()
        deploy_vars.update(vars)

        version = self.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
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
            installation_options = '{environment}:{configuration} -s {current_source.provider_name}:{current_source.options}'.format(
                current_source=self.current_source,
                **info
            )
            with self.change_directory(self.current_source.directory):
                self.execute(
                    'codev deploy {installation_options} --performer=local --disable-isolation --force {perform_debug}'.format(
                        installation_options=installation_options,
                        perform_debug=perform_debug
                    ), logger=command_logger, writein=dumps(deploy_vars))
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Setting up connectivity.")
            self.connect(infrastructure)
            logger.info("Installation has been successfully completed.")
            return True

    def exists(self):
        return self.isolator.exists() and self.isolator.is_started()

    def destroy(self):
        if self.isolator.is_started():
            self.isolator.stop()
        return self.isolator.destroy()

    @property
    def info(self):
        info = dict(
            current_source=self.current_source.name,
            current_source_options=self.current_source.options,
            current_source_ident=self.current_source.ident,
        )
        if self.isolator.exists():
            info.update(dict(ident=self.isolator.ident, ip=self.isolator.ip))
        return info
