import re

from time import sleep
from codev.configuration import BaseConfiguration
from codev.machines import MachinesProvider, BaseMachinesProvider, BaseMachine
from logging import getLogger
from os import path

logger = getLogger(__name__)


class LXCMachine(BaseMachine):
    def __init__(self, *args, **kwargs):
        super(LXCMachine, self).__init__(*args, **kwargs)
        self.__container_directory = None
        self.__share_directory = None
        self.base_dir = self.working_dir = '/root'

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

    def create(self, distribution, release, ip=None):
        if not self.exists():
            architecture = self._get_architecture()
            self.performer.execute('lxc-create -t download -n {container_name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                container_name=self.ident,
                distribution=distribution,
                release=release,
                architecture=architecture
            ))
            self._configure(ip=ip)
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

    def _configure(self, ip=None):
        self.performer.execute('mkdir -p {share_directory} && chmod 7777 {share_directory}'.format(
            share_directory=self.share_directory
        ))

        if ip:
            template_dir = 'static'
            self.performer.send_file(
                '{directory}/templates/{template_dir}/network_interfaces'.format(
                    directory=path.dirname(__file__),
                    template_dir=template_dir
                ),
                '{container_root}/etc/network/interfaces '.format(
                    container_root=self.container_root
                )
            )
        else:
            template_dir = 'default'

        for line in open('{directory}/templates/{template_dir}/config'.format(
                directory=path.dirname(__file__),
                template_dir=template_dir
            )
        ):
            self.performer.execute('echo "{line}" >> {container_config}'.format(
                    line=line.format(
                        ip=ip,
                        share_directory=self.share_directory
                    ),
                    container_config=self.container_config
                )
            )

    @property
    def share_directory(self):
        if not self.__share_directory:
            # abs_base_dir = self.performer.execute('pwd')
            abs_base_dir = '$HOME/.local/codev'
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
            'lxc-attach -n {container_name} -v HOME={base_dir} -- bash -c "cd {working_dir} && {command}"'.format(
                base_dir=self.base_dir,
                working_dir=self.working_dir,
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
    counter = 0

    def _machine(self, ident, create=False, pub_key=None, ip=None):
        machine = LXCMachine(self.performer, ident=ident)
        if create:
            machine.create(self.configuration.distribution, self.configuration.release, ip=ip)

        machine.start()

        if create:
            #install ssh server
            machine.install_package('openssh-server')

            #authorize user for ssh
            if pub_key:
                machine.execute('mkdir -p .ssh')
                machine.execute('tee .ssh/authorized_keys', writein=pub_key)

        return machine

    def machines(self, create=False, pub_key=None):
        machines = []

        ip_nums = None
        for line in self.performer.execute('cat /etc/default/lxc-net').splitlines():
            r = re.match('^LXC_ADDR=\"([\w\.]+)\"$', line)
            if r:
                ip_nums = list(map(int, r.group(1).split('.')))

        for i in range(1, self.configuration.number + 1):
            # TODO try lxc-clone instead of this
            ident = '%s_%000d' % (self.machines_name, i)
            if create and ip_nums:
                ip = '.'.join(map(str, ip_nums[:3] + [ip_nums[3] + self.counter + i]))
                self.counter += 1
            else:
                ip = None
            machine = self._machine(ident, create=create, pub_key=pub_key, ip=ip)
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
