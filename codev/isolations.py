from .machines import LXCMachine
from time import sleep
from .provider import BaseProvider


class BaseIsolationProvider(object):
    def __init__(self, performer, ident):
        self.performer = performer
        self.ident = ident


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, performer, ident):
        super(LXCIsolationProvider, self).__init__(performer, ident)
        self._lxc_machine = None


    def isolation(self):
        if self._lxc_machine:
            return self._lxc_machine

        architecture = self.performer.execute('uname -m').strip()
        if architecture == 'x86_64':
            architecture = 'amd64'

        self._lxc_machine = LXCMachine(self.performer, self.ident, 'ubuntu', 'wily', architecture)

        created = self._lxc_machine.create()
        if created:
            is_root = int(self.performer.execute('id -u')) == 0
            if is_root:
                lxc_config = '/var/lib/lxc/%s/config'
            else:
                lxc_config = '~/.local/share/lxc/%s/config'
            lxc_config = lxc_config % self.ident

            self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
            self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)

        self._lxc_machine.start()
        while not self._lxc_machine.ip:
            sleep(0.5)
            #TODO TIMEOUT

        if created:
            self._lxc_machine.execute('apt-get update')
            self._lxc_machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes -qq"')

        return self._lxc_machine


class IsolationProvider(BaseProvider):
    provider_class = BaseIsolationProvider

IsolationProvider.register('lxc', LXCIsolationProvider)




