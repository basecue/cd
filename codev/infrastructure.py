from .machines import MachinesProvider
from .provision import Provision
from .performer import Performer, CommandError
from .configuration import DictConfiguration
from logging import getLogger

logger = getLogger(__name__)
import re


class Infrastructure(object):
    def __init__(self, performer, name, configuration):
        self.name = name
        self.configuration = configuration

        self.performer = performer
        self.scripts = configuration.provision.scripts

        self._provision_provider = Provision(
            configuration.provision.provider,
            self.performer,
            self.name,
            configuration_data=configuration.provision.specific
        )

    def _machines_groups(self, performer, create=False):
        machines_groups = {}
        for machines_name, machines_configuration in self.configuration.machines.items():
            machines_provider = MachinesProvider(
                machines_configuration.provider,
                machines_name, performer, configuration_data=machines_configuration.specific
            )
            machines_groups[machines_name] = machines_provider.machines(create=create)
        return machines_groups

    def provision(self, installation):
        with self.performer.change_directory(installation.directory):
            self.performer.run_scripts(self.scripts.onstart)
        try:
            logger.info('Installing provisioner...')
            self._provision_provider.install()

            logger.info('Creating machines...')
            machines_groups = self._machines_groups(self.performer, create=True)

            logger.info('Starting provisioning...')
            self._provision_provider.run(machines_groups)
        except CommandError as e:
            logger.error(e)
            with self.performer.change_directory(installation.directory):
                self.performer.run_scripts(
                    self.scripts.onerror,
                    dict(
                        command=e.command,
                        exit_code=e.exit_code,
                        error=e.error
                    )
                )
            return False
        else:
            with self.performer.change_directory(installation.directory):
                self.performer.run_scripts(self.scripts.onsuccess)
            return True

    def connect(self, isolation):
        """
        TODO podivat se jestli je nutno mit performer a jestli je tedy nutno byt v teto class
        :param isolation:
        :return:
        """
        print(self.configuration.connectivity)
        for machine_str, connectivity_conf in self.configuration.connectivity.items():
            print(machine_str, connectivity_conf)
            r = re.match('(?P<machine_group>[^\[]+)\[(?P<machine_index>\d+)\]', machine_str)
            if r:
                machines_groups = self._machines_groups(isolation, create=False)
                machine_group = r.group('machine_group')
                machine_index = int(r.group('machine_index'))
                machine = machines_groups[machine_group][machine_index]

                for source_port, target_port in connectivity_conf.items():
                    redirection = dict(
                        source_port=source_port,
                        target_port=target_port,
                        source_ip=machine.ip,
                        target_ip=isolation.ip
                    )

                    isolation.execute('iptables -t nat -A PREROUTING --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
                    isolation.execute('iptables -t nat -A POSTROUTING -p tcp --dst {source_ip} --dport {source_port} -j SNAT --to-source {target_ip}'.format(**redirection))
                    isolation.execute('iptables -t nat -A OUTPUT --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
