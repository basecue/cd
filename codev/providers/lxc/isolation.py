from codev.isolation import BaseIsolationProvider, IsolationProvider

from .machines import LXCMachine


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._lxc_machine = None

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

    def _machine(self):
        architecture = self._get_architecture()
        return LXCMachine(self.performer, self.ident, 'ubuntu', 'wily', architecture)

    # def get_isolation(self, ident):
    #     machine = self._machine(ident)
    #     if machine.exists() and machine.is_started():
    #         return machine
    #     else:
    #         return None

    def create_isolation(self):
        machine = self._machine()

        created = machine.create()

        if created:
            self._enable_container_nesting()

        machine.start()

        if created:
            machine.execute('apt-get update')
            machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return machine


IsolationProvider.register('lxc', LXCIsolationProvider)
