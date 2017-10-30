from codev.core.providers.machines.lxc import LXCMachine, LXCMachinesSettings

from codev.control.isolation import PrivilegedIsolation


class LXCIsolation(PrivilegedIsolation):
    provider_name = 'lxc'

    def get(self, ident):
        return PrivilegedIsolation(performer=LXCMachine(performer=self.performer, ident=ident))

    def exists(self):
        return self.get(ident).exists()

    def create(self):
        isolation = self.get(ident)

        settings = LXCMachinesSettings(data=dict(distribution='ubuntu', release='xenial'))
        isolation.create(settings)
        isolation.start()

        # TODO - providers requirements
        isolation.install_packages(
            'lxc',
            'python3-pip', 'libffi-dev', 'libssl-dev',  # for codev
            'python-virtualenv', 'python-dev', 'python3-venv', 'sshpass',  # for ansible task
            'git',  # for git source
            'clsync',  # for share support
        )

        isolation.stop()
        isolation.start()
        return isolation

