from json import dumps
from logging import getLogger

from codev.core import Codev
from codev.core.debug import DebugSettings
from codev.core.executor import CommandError, Executor
from codev.core.machines import BaseMachine
from codev.core.provider import Provider
from codev.core.settings import ListDictSettings, ProviderSettings, BaseSettings, HasSettings
from codev.core.source import Source
from codev.core.utils import Ident, Status
from .log import logging_config

# from codev.core.isolator import Isolator

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')

# FIXME
"""
protocol:

call: codev-source {source_name}:{source_option} -- {source_settings_data}
return: .codev

codev-perform run {configuration_name}:{configuration_option} --force
"""


class Isolation(Provider, BaseMachine):
    def __init__(self, *args, source, next_source, configuration_name, configuration_option, **kwargs):
        self.configuration_name = configuration_name
        self.configuration_option = configuration_option
        self.source = source
        self.next_source = next_source
        super().__init__(*args, **kwargs)

    @property
    def current_source(self):
        if not self.next_source or not self.exists():
            return self.source
        else:
            return self.next_source

    def _codev_source(self):
        self.current_source.install(self)
        with self.open_file('.codev') as codev_file:
            codev = Codev.from_yaml(codev_file, configuration_name=self.configuration_name, configuration_option=self.configuration_option)

        return codev

    def _call_codev(self, subcommand, load_vars=None):
        if DebugSettings.perform_settings:
            perform_debug = ' '.join(
                (
                    f'--debug {key} {value}'
                    for key, value in DebugSettings.perform_settings.data.items()
                )
            )
        else:
            perform_debug = ''

        logging_config(control_perform=True)

        return self.execute(
            f'codev-{subcommand} {self.configuration_name}:{self.configuration_option} {perform_debug}',
            output_logger=command_logger,
            writein=dumps(load_vars or {})
        )

    def _codev_perform(self, load_vars):

        try:
            self._call_codev('perform', load_vars=load_vars)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Setting up connectivity.")
            # self.connect() TODO
            logger.info("Installation has been successfully completed.")
            return True
        # finally:
        #     logger.info("Setting up connectivity.")
        #     # self.connect()
        #     # FIXME

    def _codev_install(self, version):
        pass

    def perform(self, input_vars):
        codev = self._codev_source()

        self._codev_install(codev.version)

        load_vars = {**codev.configuration.loaded_vars, **input_vars}
        load_vars.update(DebugSettings.settings.load_vars)

        self._codev_perform(load_vars)

        # FIXME
        # version = self.executor.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
        # logger.info("Run 'codev {version}' in isolation.".format(version=version))

    @property
    def status(self):

        status = Status(
            source=self.source.status,
            next_source=self.next_source.status
        )

        if self.exists():
            status.update(
                status=self._call_codev('status') # TODO
            )
        return status


class IsolationScriptsSettings(BaseSettings):
    @property
    def oncreate(self):
        return ListDictSettings(self.data.get('oncreate', []))

    @property
    def onenter(self):
        return ListDictSettings(self.data.get('onenter', []))


class IsolationProviderSettings(ProviderSettings):

    @property
    def executor(self):
        return ProviderSettings(self.data.get('executor', {}))

    @property
    def connectivity(self):
        return ListDictSettings(self.data.get('connectivity', {}))

    @property
    def scripts(self):
        return IsolationScriptsSettings(self.data.get('scripts', {}))

    @property
    def sources(self):
        return ListDictSettings(
            self.data.get('sources', [])
        )


class IsolationProvider(HasSettings):
    settings_class = IsolationProviderSettings

    def __init__(
        self,
        *args,
        project_name,
        configuration_name,
        configuration_option,
        source_name,
        source_option,
        next_source_name,
        next_source_option,
        **kwargs
    ):

        self.configuration_name = configuration_name
        self.configuration_option = configuration_option

        self.source_name = source_name
        self.source_option = source_option
        self.next_source_name = next_source_name
        self.next_source_option = next_source_option

        self.ident = Ident(
            project_name,
            configuration_name,
            configuration_option,
            source_name,
            source_option,
            next_source_name,
            next_source_option,
        )

        super().__init__(*args, **kwargs)

    def isolation(self):
        executor_provider = self.settings.executor.provider
        executor_settings_data = self.settings.executor.settings_data

        executor = Executor(
            executor_provider,
            settings_data=executor_settings_data
        )

        return Isolation(
            self.settings.provider,
            executor=executor,
            settings_data=self.settings.settings_data,
            ident=self.ident,
            configuration_name=self.configuration_name,
            configuration_option=self.configuration_option,
            source=self._get_source(self.source_name, self.source_option),
            next_source=self._get_source(self.next_source_name, self.next_source_option, default=False)
        )

    def _get_source(self, source_name, source_option, default=True):
        # TODO refactor
        try:
            return Source.get(source_name, self.settings.sources, source_option, default=default)
        except ValueError:
            raise ValueError(
                "Source '{source_name}' is not allowed source.".format(
                    source_name=source_name,
                )
            )


class PrivilegedIsolation(Isolation):

    def _codev_install(self, version):

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



# class IsolationX(object):
#     def __init__(self, isolation_settings, infrastructure_settings, source, next_source, executor, ident):
#
#         ident = ':'.join(ident) if ident else str(time())
#         ident_hash = sha256(ident.encode()).hexdigest()
#
#         self.isolator = Isolator(
#             isolation_settings.provider,
#             executor=executor,
#             settings_data=isolation_settings.settings_data,
#             ident=ident_hash
#         )
#         self.settings = isolation_settings
#         self.source = source
#         self.next_source = next_source
#         self.current_source = self.next_source if self.next_source and self.exists() else self.source
#
#         self.infrastructure = Infrastructure(self.isolator, infrastructure_settings)
#
#     def connect(self):
#         """
#         :param isolation:
#         :return:
#         """
#         for machine_ident, connectivity_conf in self.settings.connectivity.items():
#             machine = self.infrastructure.get_machine_by_ident(machine_ident)
#
#             for source_port, target_port in connectivity_conf.items():
#                 self.isolator.redirect(machine.ip, source_port, target_port)
#
#     def _install_codev(self, codev_file):
#         version = YAMLSettingsReader().from_yaml(codev_file).version
#         self.isolator.execute('pip3 install setuptools')
#
#         # uninstall previous version of codev (ignore if not installed)
#         self.isolator.check_execute('pip3 uninstall codev -y')
#
#         # install proper version of codev
#         # TODO requirements - 'python3-pip', 'libffi-dev', 'libssl-dev'
#         if not DebugSettings.settings.distfile:
#             logger.debug("Install codev version '{version}' to isolation.".format(version=version))
#             self.isolator.execute('pip3 install --upgrade codev=={version}'.format(version=version))
#         else:
#             distfile = DebugSettings.settings.distfile.format(version=version)
#             debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
#
#             from os.path import basename
#             remote_distfile = '/tmp/{distfile}'.format(distfile=basename(distfile))
#
#             self.isolator.send_file(distfile, remote_distfile)
#             self.isolator.execute('pip3 install --upgrade {distfile}'.format(distfile=remote_distfile))
#
#     # def execute_script(self, script, arguments=None, logger=None):
#     #     if DebugSettings.perform_settings:
#     #         perform_debug = ' '.join(
#     #             (
#     #                 '--debug {key} {value}'.format(key=key, value=value)
#     #                 for key, value in DebugSettings.perform_settings.data.items()
#     #             )
#     #         )
#     #     else:
#     #         perform_debug = ''
#     #     arguments.update(self.status)
#     #     codev_script = 'codev-perform execute {environment}:{configuration} {perform_debug} -- {script}'.format(
#     #         script=script,
#     #         environment=arguments['environment'],
#     #         configuration=arguments['configuration'],
#     #         source=arguments['source'],
#     #         source_option=arguments['source_option'],
#     #         perform_debug=perform_debug
#     #     )
#     #     with self.change_directory(self.current_source.directory):
#     #         super().execute_script(codev_script, arguments=arguments, logger=logger)
#
#     def _install_project(self):
#         # TODO refactorize
#         self.current_source.install(self.isolator)
#
#         # load .codev file from source and install codev with specific version
#         with self.current_source.open_codev_file(self.isolator) as codev_file:
#             self._install_codev(codev_file)
#
#     def install(self, status):
#         # TODO refactorize - divide?
#         if not self.isolator.exists():
#             logger.info("Creating isolation...")
#             self.isolator.create()
#             created = True
#         else:
#             if not self.isolator.is_started():
#                 self.isolator.start()
#             created = False
#
#         if created or not self.next_source:
#             logger.info("Install project from source to isolation...")
#             self.current_source = self.source
#             self._install_project()
#
#             # self.execute_scripts(self.settings.scripts.oncreate, status, logger=command_logger)
#         else:  # if not created and self.next_source
#             logger.info("Transition source in isolation...")
#             self.current_source = self.next_source
#             self._install_project()
#
#         logger.info("Entering isolation...")
#         # TODO
#         # self.execute_scripts(self.settings.scripts.onenter, status, logger=command_logger)
#
#     def run(self, status, input_vars):
#
#         # copy and update loaded_vars
#         load_vars = {**self.settings.loaded_vars, **input_vars}
#
#         version = self.isolator.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
#         logger.info("Run 'codev {version}' in isolation.".format(version=version))
#
#         if DebugSettings.perform_settings:
#             perform_debug = ' '.join(
#                 (
#                     '--debug {key} {value}'.format(key=key, value=value)
#                     for key, value in DebugSettings.perform_settings.data.items()
#                 )
#             )
#         else:
#             perform_debug = ''
#
#         logging_config(control_perform=True)
#         try:
#             configuration = '{configuration}:{configuration_option}'.format(
#                 **status
#             )
#             with self.isolator.change_directory(self.current_source.directory):
#                 self.isolator.execute(
#                     'codev-perform run {configuration} --force {perform_debug}'.format(
#                         configuration=configuration,
#                         perform_debug=perform_debug
#                     ), logger=command_logger, writein=dumps(load_vars))
#         except CommandError as e:
#             command_logger.error(e.error)
#             logger.error("Installation failed.")
#             return False
#         else:
#             logger.info("Installation has been successfully completed.")
#             return True
#         finally:
#             logger.info("Setting up connectivity.")
#             self.connect()
#
#     def destroy(self):
#         if self.isolator.is_started():
#             self.isolator.stop()
#         return self.isolator.destroy()
#
#     def exists(self):
#         return self.isolator.exists()
#
#     @property
#     def status(self):
#         if self.exists() and self.isolator.is_started():
#             infrastructure_status = self.infrastructure.status
#         else:
#             infrastructure_status = {}
#
#         status = dict(
#             current_source=self.current_source.name,
#             current_source_option=self.current_source.option,
#             infrastructure=infrastructure_status
#         )
#         if self.isolator.exists():
#             status.update(dict(ident=self.isolator.ident, ip=self.isolator.ip))
#         return status
