from codev.isolation import BaseIsolationProvider, IsolationProvider

from .machines import LXCMachine


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._machine = None

    def _enable_container_nesting(self):
        lxc_config = '{container_directory}config'.format(
            self.machine.container_directory
        )

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    @property
    def machine(self):
        if not self._machine:
            architecture = self._get_architecture()
            self._machine = LXCMachine(self.performer, self.ident, 'ubuntu', 'wily', architecture)
        return self._machine

    def create_isolation(self):
        created = self.machine.create()

        if created:
            self._enable_container_nesting()

        self.machine.start()

        if created:
            self.machine.execute('apt-get update')
            self.machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return self.machine


IsolationProvider.register('lxc', LXCIsolationProvider)
