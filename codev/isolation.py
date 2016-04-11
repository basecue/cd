import re
from .settings import YAMLSettingsReader
from logging import getLogger
from .debug import DebugSettings
from .performer import BaseRunner

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


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
                    self.isolator.redirect(machine, source_port, target_port)

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
            with self.isolator.change_directory(current_source.directory):
                self.isolator.run_scripts(self.scripts.oncreate)
        else:
            if self.next_source:
                logger.info("Transition source in isolation.")
                current_source = self.next_source
                current_source.install(self.isolator)
                self.install_codev(current_source)
        with self.isolator.change_directory(current_source.directory):
            self.isolator.run_scripts(self.scripts.onenter)
        return current_source
