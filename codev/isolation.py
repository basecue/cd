from logging import getLogger

from .settings import YAMLSettingsReader
from .performer import BaseProxyPerformer
from .logging import logging_config
from .performer import CommandError
from .debug import DebugSettings


logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Isolation(BaseProxyPerformer):
    def __init__(self, settings, source, next_source, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = self.performer
        self.connectivity = settings.connectivity
        self.scripts = settings.scripts
        self.source = source
        self.next_source = next_source
        self.current_source = self.next_source if self.next_source and self.exists() else self.source

    def connect(self, infrastructure):
        """
        :param isolation:
        :return:
        """
        for machine_ident, connectivity_conf in self.connectivity.items():
            machine = infrastructure.get_machine_by_ident(machine_ident)

            for source_port, target_port in connectivity_conf.items():
                self.isolator.redirect(machine.ip, source_port, target_port)

    def _install_codev(self):
        with self.change_directory(self.current_source.directory):
            with self.get_fo('.codev') as codev_file:
                version = YAMLSettingsReader().from_yaml(codev_file).version

        self.execute('pip3 install setuptools')

        # install proper version of codev
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

    def run_script(self, script, arguments=None, logger=None):
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
        codev_script = 'codev run -e {environment} -c {configuration} -s {source}:{source_options} --performer=local --disable-isolation {perform_debug} -- {script}'.format(
            script=script,
            environment=arguments['environment'],
            configuration=arguments['configuration'],
            source=arguments['source'],
            source_options=arguments['source_options'],
            perform_debug=perform_debug
        )
        with self.change_directory(self.current_source.directory):
            super().run_script(codev_script, arguments=arguments, logger=logger)

    def install(self, info):
        if not self.isolator.exists():
            logger.info("Creating isolation...")
            self.isolator.create()
            created = True
        else:
            created = False

        self.current_source = self.source
        if created:
            logger.info("Install project to isolation...")
            self.current_source.install(self.performer)
            self._install_codev()
            self.run_scripts(self.scripts.oncreate, info, logger=command_logger)
        else:
            if self.next_source:
                logger.info("Transition source in isolation...")
                self.current_source = self.next_source
                self.current_source.install(self.performer)
                self._install_codev()
        logger.info("Entering isolation...")
        self.run_scripts(self.scripts.onenter, info, logger=command_logger)

    def deploy(self, infrastructure, info):
        version = self.performer.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
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
                current_source=self.current_source,
                **info
            )
            with self.performer.change_directory(self.current_source.directory):
                self.performer.execute(
                    'codev deploy {installation_options} --performer=local --disable-isolation --force {perform_debug}'.format(
                        installation_options=installation_options,
                        perform_debug=perform_debug
                    ), logger=command_logger)
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
        return self.isolator.exists()

    def destroy(self):
        return self.isolator.destroy()

    def is_started(self):
        return self.isolator.is_started()

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
