import re

from time import sleep
from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider, BaseMachine


class LXCMachine(BaseMachine):
    def __init__(self, *args, **kwargs):
        super(LXCMachine, self).__init__(*args, **kwargs)
        self.__container_directory = None
        self.__share_directory = None
        self.base_dir = '/root'

    def exists(self):
        output = self.performer.execute('lxc-ls')
        return self.ident in output.split()

    def is_started(self):
        output = self.performer.execute('lxc-info -n {container_name} -s'.format(
            container_name=self.ident,
        ))

        r = re.match('^State:\s+(.*)$', output.strip())
        if r:
            state = r.group(1)
        else:
            raise ValueError('o:%s:o' % output)

        if state == 'RUNNING':
            return True
        elif state == 'STOPPED':
            return False
        else:
            raise ValueError('s:%s:s' % state)

    def create(self, distribution, release):
        if not self.exists():
            architecture = self._get_architecture()
            self.performer.execute('lxc-create -t download -n {container_name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                container_name=self.ident,
                distribution=distribution,
                release=release,
                architecture=architecture
            ))
            self._configure()
            return True
        else:
            return False

    def destroy(self):
        if self.exists():
            self.stop()
            self.performer.execute('lxc-destroy -n {container_name}'.format(
                container_name=self.ident,
            ))
            return True
        else:
            return False

    def _get_architecture(self):
        architecture = self.performer.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    def _configure(self):

        self.performer.execute('echo "lxc.mount.auto = cgroup" >> {container_config}'.format(
            container_config=self.container_config
        ))

        self.performer.execute('echo "lxc.aa_profile = lxc-container-default-with-nesting" >> {container_config}'.format(
            container_config=self.container_config
        ))

        self.performer.execute('mkdir -p {share_directory} && chmod 7777 {share_directory}'.format(
            share_directory=self.share_directory
        ))

        self.performer.execute(
            'echo "lxc.mount.entry = {share_directory} share none bind,create=dir 0.0" >> {container_config}'.format(
                share_directory=self.share_directory,
                container_config=self.container_config
            )
        )

    @property
    def share_directory(self):
        if not self.__share_directory:
            abs_base_dir = self.performer.execute('pwd')
            return '{abs_base_dir}/{container_name}/share'.format(
                abs_base_dir=abs_base_dir,
                container_name=self.ident
            )
        return self.__share_directory

    @property
    def _container_directory(self):
        if not self.__container_directory:
            lxc_path = self.performer.execute('lxc-config lxc.lxcpath')
            self.__container_directory = '{lxc_path}/{container_name}'.format(
                lxc_path=lxc_path,
                container_name=self.ident
            )
        return self.__container_directory

    @property
    def container_root(self):
        return '{container_directory}/rootfs'.format(container_directory=self._container_directory)

    @property
    def container_config(self):
        return '{container_directory}/config'.format(container_directory=self._container_directory)

    def start(self):
        if not self.is_started():
            self.performer.execute('lxc-start -n {container_name}'.format(
                container_name=self.ident,
            ))

            while not self.ip:
                sleep(0.5)

            return True
        else:
            return False

    def stop(self):
        if self.is_started():
            self.performer.execute('lxc-stop -n {container_name}'.format(
                container_name=self.ident,
            ))

            return True
        else:
            return False

    @property
    def ip(self):
        output = self.performer.execute('lxc-info -n {container_name} -i'.format(
            container_name=self.ident,
        ))

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

    @property
    def host(self):
        return self.ip

    def execute(self, command, logger=None, writein=None):
        output = self.performer.execute(
            'lxc-attach -n {container_name} -v HOME={base_dir} -- bash -c "cd {base_dir} && {command}"'.format(
                base_dir=self.base_dir,
                container_name=self.ident,
                command=command,
            ), logger=logger, writein=writein
        )
        return output


class LXCMachinesConfiguration(BaseConfiguration):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def number(self):
        return int(self.data.get('number', 1))


class LXCMachinesProvider(BaseMachinesProvider):
    configuration_class = LXCMachinesConfiguration

    def _create_machine(self, ident):
        machine = LXCMachine(self.performer, ident=ident)
        machine.create(self.configuration.distribution, self.configuration.release)
        machine.start()

        #install ssh server
        machine.install_package('openssh-server')

        #authorize user for ssh
        pub_key = '%s\n' % self.performer.execute('ssh-add -L')
        machine.execute('mkdir -p ~/.ssh')
        machine.execute('tee ~/.ssh/authorized_keys', writein=pub_key)

        #add machine ssh signature to known_hosts
        machine.performer.execute('ssh-keyscan -H {host} >> ~/.ssh/known_hosts'.format(host=machine.host))
        return machine

    def create_machines(self):
        machines = []
        for i in range(1, self.configuration.number + 1):
            # TODO try lxc-clone instead of this
            ident = '%s_%000d' % (self.machines_name, i)
            machine = self._create_machine(ident)
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
