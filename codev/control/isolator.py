from json import dumps
from hashlib import sha256
from logging import getLogger
from time import time

from codev.core.performer import CommandError, ProxyPerformer
from codev.core.provider import Provider, ConfigurableProvider
from codev.core.settings import YAMLSettingsReader
from codev.core.debug import DebugSettings

# from codev.core.isolator import Isolator
from codev.core.infrastructure import Infrastructure

from .log import logging_config

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Isolator(Provider, ConfigurableProvider, ProxyPerformer):
    def get_or_create(self, ident):
        if self.exists(ident):
            return self.get(ident), False
        else:
            return self.create(ident), True

    def get_or_none(self, ident):
        if self.isolator.exists(ident):
            return self.isolator.get(ident)
        else:
            return None

    def exists(self, ident):
        raise NotImplementedError()

    def get(self, ident):
        raise NotImplementedError()

    def create(self, ident):
        raise NotImplementedError()


class Isolation(ProxyPerformer):

    def install(self, version):
        raise NotImplementedError()

    def perform(self, configuration_name, configuration_option, input_vars):

        # FIXME
        # version = self.performer.execute('pip3 show codev | grep ^Version | cut -d " " -f 2')
        # logger.info("Run 'codev {version}' in isolation.".format(version=version))

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
            self.execute(
                'codev-perform run {configuration_name}:{configuration_option} --force {perform_debug}'.format(
                    configuration_name=configuration_name,
                    configuration_option=configuration_option,
                    perform_debug=perform_debug
                ), logger=command_logger, writein=dumps(input_vars))
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Installation has been successfully completed.")
            return True
        finally:
            logger.info("Setting up connectivity.")
            # self.connect()
            # FIXME


class PrivilegedIsolation(Isolation):
    def install(self, version):
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
#     def __init__(self, isolation_settings, infrastructure_settings, source, next_source, performer, ident):
#
#         ident = ':'.join(ident) if ident else str(time())
#         ident_hash = sha256(ident.encode()).hexdigest()
#
#         self.isolator = Isolator(
#             isolation_settings.provider,
#             performer=performer,
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
#     #         source_options=arguments['source_options'],
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
#             current_source_options=self.current_source.options,
#             infrastructure=infrastructure_status
#         )
#         if self.isolator.exists():
#             status.update(dict(ident=self.isolator.ident, ip=self.isolator.ip))
#         return status
