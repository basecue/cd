from codev.isolation import BaseIsolationProvider, IsolationProvider

from .machines import LXCMachine


class LXCIsolationProvider(BaseIsolationProvider):
    def __init__(self, *args, **kwargs):
        super(LXCIsolationProvider, self).__init__(*args, **kwargs)
        self._machine = None

    def configure_container(self):
        lxc_config = '{container_directory}config'.format(
            container_directory=self.machine.container_directory
        )

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> %s' % lxc_config)
        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> %s' % lxc_config)


        self.performer.execute('mkdir -p {isolation_ident}/share && chmod 7777 {isolation_ident}/share'.format(
            isolation_ident=self.ident
        ))
        home_dir = self.performer.execute('pwd')
        self.performer.execute(
            'echo "lxc.mount.entry = {home_dir}/{isolation_ident}/share share none ro,bind 0.0" >> {lxc_config}'.format(
                home_dir=home_dir,
                isolation_ident=self.ident,
                lxc_config=lxc_config
            )
        )
        self.performer.execute('lxc-usernsexec -- mkdir -p {container_directory}/rootfs/share'.format(
            container_directory=self.machine.container_directory
        ))

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
            self.configure_container()

        self.machine.start()

        if created:
            self.machine.execute('apt-get update')
            self.machine.execute('bash -c "DEBIAN_FRONTEND=noninteractive apt-get install lxc -y --force-yes"')

        return self.machine


IsolationProvider.register('lxc', LXCIsolationProvider)
