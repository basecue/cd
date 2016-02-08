from codev.isolation import BaseIsolationProvider, IsolationProvider

from .machines import LXCMachine
from time import sleep


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, ident):
        super(LXCIsolationProvider, self).__init__(ident)
        self._lxc_machine = None
        self.performer = None

    def _enable_container_nesting(self):
        is_root = int(self.performer.execute('id -u')) == 0
        if is_root:
            lxc_config = '/var/lib/lxc/%s/config'
        else:
            lxc_config = '~/.local/share/lxc/%s/config'
        lxc_config = lxc_config % self.ident

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    def _install_lxc(self):
        self._lxc_machine.execute('apt-get update')
        self._lxc_machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

    def isolation(self, performer):
        if self._lxc_machine:
            return self._lxc_machine

        self.performer = performer
        architecture = self._get_architecture()

        self._lxc_machine = LXCMachine(self.performer, self.ident, 'ubuntu', 'wily', architecture)

        created = self._lxc_machine.create()

        if created:
            self._enable_container_nesting()

        self._lxc_machine.start()

        #waiting for networking
        while not self._lxc_machine.ip:
            sleep(0.5)
            #TODO TIMEOUT

        if created:
            self._install_lxc()

        return self._lxc_machine


IsolationProvider.register('lxc', LXCIsolationProvider)
