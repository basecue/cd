import re
from .settings import YAMLSettingsReader
from logging import getLogger
from .debug import DebugSettings
from .performer import BaseProxyPerformer

logger = getLogger(__name__)
command_logger = getLogger('command')
debug_logger = getLogger('debug')


class Isolation(BaseProxyPerformer):
    def __init__(self, settings, deployment_info, *args, **kwargs):
        super(Isolation, self).__init__(*args, **kwargs)
        self.isolator = self.performer
        self.connectivity = settings.connectivity
        self.scripts = settings.scripts
        self.deployment_info = deployment_info

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
        with self.change_directory(source.directory):
            with self.get_fo('.codev') as codev_file:
                version = YAMLSettingsReader().from_yaml(codev_file).version

        # install python3 pip
        self.install_packages('python3-pip')
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
        codev_script = 'codev run {script} -e {environment} -c {configuration} -s {source}:{source_options} --performer=local --isolator=none'.format(
            script=script,
            environment=self.deployment_info['environment'],
            configuration=self.deployment_info['configuration'],
            source=self.deployment_info['source'],
            source_options=self.deployment_info['source_options']
        )
        super(Isolation, self).run_script(codev_script, arguments=arguments, logger=logger)

    def install(self, source, next_source):
        created = self.isolator.create()

        current_source = source
        if created:
            logger.info("Install project to isolation.")
            current_source.install(self.performer)
            self.install_codev(current_source)
            with self.change_directory(current_source.directory):
                self.run_scripts(self.scripts.oncreate, current_source)
        else:
            if next_source:
                logger.info("Transition source in isolation.")
                current_source = next_source
                current_source.install(self.performer)
                self.install_codev(current_source)
        self.run_scripts(self.scripts.onenter, current_source)
        return current_source
