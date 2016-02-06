from .machines import LXCMachine
from time import sleep


class LXCIsolation(LXCMachine):
    def __init__(self, performer, ident):
        performer = performer
        self.ident = ident
        architecture = performer.execute('uname -m').strip()
        if architecture == 'x86_64':
            architecture = 'amd64'
        super(LXCIsolation, self).__init__(performer, ident, 'ubuntu', 'wily', architecture)
        self._after()

    def _after(self):
        created = self.create()
        if created:
            is_root = int(self.performer.execute('id -u')) == 0
            if is_root:
                lxc_config = '/var/lib/lxc/%s/config'
            else:
                lxc_config = '~/.local/share/lxc/%s/config'
            lxc_config = lxc_config % self.ident

            self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
            self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)

        self.start()
        while not self.ip:
            sleep(0.5)
            #TODO TIMEOUT

        if created:
            self.execute('apt-get update')
            self.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes -qq"')


ISOLATION_BY_NAME = {
    'lxc': LXCIsolation
}


class Isolation(object):
    def __new__(cls, performer, provider, ident):
        return ISOLATION_BY_NAME[provider](performer, ident)

