import re
from .provider import BaseProvider
from .performer import BaseRunner, BasePerformer, CommandError
from .debug import DebugConfiguration
from .configuration import YAMLConfigurationReader
from logging import getLogger
from .logging import logging_config

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class IsolationError(Exception):
    pass


class BaseIsolation(BaseRunner, BasePerformer):
    def __init__(self, scripts, connectivity, infrastructure, installation, next_installation, *args, **kwargs):
        super(BaseIsolation, self).__init__(*args, **kwargs)
        self.connectivity = connectivity
        self.infrastructure = infrastructure
        self.installation = installation
        self.next_installation = next_installation
        self.scripts = scripts

    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def execute(self, command, logger=None, writein=None, max_lines=None):
        raise NotImplementedError()

    def make_link(self, source, target):
        # experimental
        raise NotImplementedError()

    @property
    def ip(self):
        raise NotImplementedError()

    def connect(self):
        """
        :param isolation:
        :return:
        """
        for machine_str, connectivity_conf in self.connectivity.items():
            r = re.match('^(?P<machine_group>[^\[]+)_(?P<machine_index>\d+)$', machine_str)
            if r:
                machines_groups = self.infrastructure.machines_groups(self, create=False)
                machine_group = r.group('machine_group')
                machine_index = int(r.group('machine_index')) - 1
                machine = machines_groups[machine_group][machine_index]

                for source_port, target_port in connectivity_conf.items():
                    redirection = dict(
                        source_port=source_port,
                        target_port=target_port,
                        source_ip=machine.ip,
                        target_ip=self.ip
                    )

                    self.execute('iptables -t nat -A PREROUTING --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
                    self.execute('iptables -t nat -A POSTROUTING -p tcp --dst {source_ip} --dport {source_port} -j SNAT --to-source {target_ip}'.format(**redirection))
                    self.execute('iptables -t nat -A OUTPUT --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
    
    def run_script(self, script, arguments=None, logger=None):
        if arguments is None:
            arguments = {}

        for machine_group_name, machines in self.infrastructure.machines_groups(self).items():
            for machine in machines:
                arguments['machine_{ident}'.format(ident=machine.ident)] = machine.ip

        super(BaseIsolation, self).run_script(script, arguments=arguments, logger=logger)
    
    def enter(self, create=False, next_install=False):
        current_installation = self.installation
        if create:
            logger.info("Creating isolation...")
            if self.create():
                logger.info("Install project to isolation.")
                current_installation.install(self)

                # run oncreate scripts
                with self.change_directory(current_installation.directory):
                    self.run_scripts(self.scripts.oncreate)
            else:
                if next_install and self.next_installation:
                    logger.info("Transition installation in isolation.")
                    current_installation = self.next_installation
                    current_installation.install(self)
        else:
            if not self.exists():
                raise IsolationError('No such isolation found.')

        logger.info("Entering isolation...")
        # run onenter scripts
        with self.change_directory(current_installation.directory):
            self.run_scripts(self.scripts.onenter)
        return current_installation

    def install(self, environment):

        current_installation = self.enter(create=True, next_install=True)

        with self.change_directory(current_installation.directory):
            with self.get_fo('.codev') as codev_file:
                version = YAMLConfigurationReader().from_yaml(codev_file).version

        # install python3 pip
        self.execute('apt-get install python3-pip -y --force-yes')
        self.execute('pip3 install setuptools')

        # install proper version of codev
        if not DebugConfiguration.configuration.distfile:
            logger.debug("Install codev version '{version}' to isolation.".format(version=version))
            self.execute('pip3 install --upgrade codev=={version}'.format(version=version))
        else:
            distfile = DebugConfiguration.configuration.distfile.format(version=version)
            debug_logger.info('Install codev {distfile}'.format(distfile=distfile))
            self.send_file(distfile, '/tmp/codev.tar.gz')
            self.execute('pip3 install --upgrade /tmp/codev.tar.gz')

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
            deployment_options = '-e {environment} -i {infrastructure} -s {current_installation.provider_name}:{current_installation.options}'.format(
                current_installation=current_installation,
                infrastructure=self.infrastructure.name,
                environment=environment
            )
            with self.change_directory(current_installation.directory):
                self.execute('codev deploy {deployment_options} --performer=local --disable-isolation --force {perform_debug}'.format(
                    deployment_options=deployment_options,
                    perform_debug=perform_debug
                ), logger=command_logger)
        except CommandError as e:
            command_logger.error(e.error)
            logger.error("Installation failed.")
            return False
        else:
            logger.info("Setting up connectivity.")
            self.connect()
            logger.info("Installation has been successfully completed.")
            return True


class Isolation(BaseProvider):
    provider_class = BaseIsolation
