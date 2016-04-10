from logging import getLogger
from .machines import MachinesProvider
from hashlib import md5
from .isolator import Isolator

logger = getLogger(__name__)


class Infrastructure(object):
    def __init__(self, performer, settings):
        self.performer = performer
        self.settings = settings
        self.machines_groups = {}

    def create(self):
        pub_key = '%s\n' % self.performer.execute('ssh-add -L')
        for machines_name, machines_settings in self.settings.items():
            machines_provider = MachinesProvider(
                machines_settings.provider,
                machines_name, self.performer, settings_data=machines_settings.specific
            )
            self.machines_groups[machines_name] = machines_provider.machines(create=True, pub_key=pub_key)

    def machines(self):
        for machine_group_name, machines in self.machines_groups:
            for machine in machines:
                yield machine

    def machines_info(self):
        return {
            'machine_{ident}'.format(ident=machine.ident): machine.ip for machine in self.machines()
        }

####################

import re
from .isolator import IsolatorError


class Isolation(object):
    def __init__(self, isolator, settings, source, next_source):
        self.isolator = isolator
        self.connectivity = settings.connectivity
        self.scripts = settings.scripts
        self.source = source
        self.next_source = next_source

    def connect(self, infrastructure):
        """
        :param isolation:
        :return:
        """
        for machine_str, connectivity_conf in self.connectivity.items():
            r = re.match('^(?P<machine_group>[^\[]+)_(?P<machine_index>\d+)$', machine_str)
            if r:
                machines_groups = infrastructure.machines_groups
                machine_group = r.group('machine_group')
                machine_index = int(r.group('machine_index')) - 1
                machine = machines_groups[machine_group][machine_index]

                for source_port, target_port in connectivity_conf.items():
                    # TODO move to isolator
                    redirection = dict(
                        source_port=source_port,
                        target_port=target_port,
                        source_ip=machine.ip,
                        target_ip=self.isolator.ip
                    )

                    self.isolator.execute('iptables -t nat -A PREROUTING --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
                    self.isolator.execute('iptables -t nat -A POSTROUTING -p tcp --dst {source_ip} --dport {source_port} -j SNAT --to-source {target_ip}'.format(**redirection))
                    self.isolator.execute('iptables -t nat -A OUTPUT --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))

    def install_codev(self, source):
        with self.isolator.change_directory(source.directory):
            with self.isolator.get_fo('.codev') as codev_file:
                version = YAMLSettingsReader().from_yaml(codev_file).version

        # install python3 pip
        self.isolator.install_packages('python3-pip')
        self.isolator.execute('pip3 install setuptools')

        # install proper version of codev
        if not DebugSettings.settings.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            self.isolator.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugSettings.settings.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))

            from os.path import basename
            remote_distfile = '/tmp/{distfile}'.format(distfile=basename(distfile))

            self.isolator.send_file(distfile, remote_distfile)
            self.isolator.execute('pip3 install --upgrade {distfile}'.format(distfile=remote_distfile))

    def install(self):
        created = self.isolator.create()

        current_source = self.source
        if created:
            logger.info("Install project to isolation.")
            current_source.install(self.isolator)
            self.install_codev(current_source)
            # TODO run oncreate scripts
        else:
            if self.next_source:
                logger.info("Transition source in isolation.")
                current_source = self.next_source
                current_source.install(self.isolator)
                self.install_codev(current_source)

        #TODO run onenter scripts
        return current_source


#
from .debug import DebugSettings
from .settings import YAMLSettingsReader
from logging import getLogger
from .logging import logging_config
from .performer import CommandError

command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Configuration(object):
    def __init__(self, performer, name, settings, source, next_source):
        self.name = name
        self.settings = settings
        self.performer = performer
        self._infrastructure = Infrastructure(performer, self.settings.infrastructure)
        self.isolation = Isolation(performer, self.settings.isolation, source, next_source)

    def infrastructure(self, create=False):
        if create:
            self._infrastructure.create()
        return self._infrastructure.machines_groups

    def install(self, environment):
        current_source = self.isolation.install()

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
                environment=environment
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
