import re

from time import sleep
from codev.settings import BaseSettings
from codev.machines import MachinesProvider, BaseMachinesProvider, BaseMachine
from contextlib import contextmanager
from logging import getLogger
from os import path

logger = getLogger(__name__)


class LXCMachine(BaseMachine):
    def __init__(self, *args, **kwargs):
        super(LXCMachine, self).__init__(*args, **kwargs)
        self.__container_directory = None
        self.__share_directory = None
        self.base_dir = self.working_dir = '/root'
        self.__gateway = None

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

    def create(self, distribution, release, ip=None, gateway=None):
        if not self.exists():
            architecture = self._get_architecture()
            self.performer.execute('lxc-create -t download -n {container_name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                container_name=self.ident,
                distribution=distribution,
                release=release,
                architecture=architecture
            ))
            self._configure(ip=ip, gateway=gateway)
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

    def _configure(self, ip=None, gateway=None):
        self.performer.execute('mkdir -p {share_directory} && chmod 7777 {share_directory}'.format(
            share_directory=self.share_directory
        ))
        if self.performer.check_execute('[ -f /usr/share/lxc/config/nesting.conf ]'):
            nesting = 'lxc.mount.auto = cgroup\nlxc.include = /usr/share/lxc/config/nesting.conf'
        else:
            nesting = 'lxc.mount.auto = cgroup\nlxc.aa_profile = lxc-container-default-with-nesting'

        if ip:
            template_dir = 'static'
            self.performer.send_file(
                '{directory}/templates/{template_dir}/network_interfaces'.format(
                    directory=path.dirname(__file__),
                    template_dir=template_dir
                ),
                '{container_root}/etc/network/interfaces'.format(
                    container_root=self.container_root
                )
            )
            self.performer.execute(
                'rm -f {container_root}/etc/resolv.conf'.format(
                    container_root=self.container_root
                )
            )
            self.performer.execute(
                'echo "nameserver {gateway}" >> {container_root}/etc/resolv.conf'.format(
                    gateway=gateway,
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
                        share_directory=self.share_directory,
                        nesting=nesting
                    ),
                    container_config=self.container_config
                )
            )

        # ubuntu trusty workaround
        # self.performer.execute("sed -e '/lxc.include\s=\s\/usr\/share\/lxc\/config\/ubuntu.userns\.conf/ s/^#*/#/' -i {container_config}".format(container_config=self.container_config))

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

    def _sanitize_path(self, path):
        if path.startswith('~/'):
            path = '{base_dir}/{path}'.format(
                base_dir=self.base_dir,
                path=path[2:]
            )

        if not path.startswith('/'):
            path = '{working_dir}/{path}'.format(
                working_dir=self.working_dir,
                path=path
            )
        return path

    @property
    def _gateway(self):
        if not self.__gateway:
            # attempts to get gateway ip
            for i in range(3):
                self.__gateway = self.performer.execute(
                    'lxc-attach -n {container_name} -- ip route | grep default | cut -d " " -f 3'.format(
                        container_name=self.ident
                    )
                )
                if self.__gateway:
                    break
                else:
                    sleep(3)
        return self.__gateway

    @contextmanager
    def get_fo(self, remote_path):
        tempfile = '/tmp/codev.{ident}.tempfile'.format(ident=self.ident)

        remote_path = self._sanitize_path(remote_path)

        self.performer.execute('lxc-usernsexec -- cp {container_root}{remote_path} {tempfile}'.format(
            tempfile=tempfile,
            remote_path=remote_path,
            container_root=self.container_root
        ))
        try:
            with self.performer.get_fo(tempfile) as fo:
                yield fo
        finally:
            self.performer.execute('lxc-usernsexec -- rm {tempfile}'.format(tempfile=tempfile))

    def send_file(self, source, target):
        tempfile = '/tmp/codev.{ident}.tempfile'.format(ident=self.ident)
        self.performer.send_file(source, tempfile)
        target = self._sanitize_path(target)

        self.performer.execute('lxc-usernsexec -- cp {tempfile} {container_root}{target}'.format(
            tempfile=tempfile,
            target=target,
            container_root=self.container_root
        ))
        self.performer.execute('rm {tempfile}'.format(tempfile=tempfile))

    @property
    def host(self):
        return self.ip

    def execute(self, command, env={}, logger=None, writein=None, max_lines=None):
        env.update({
            'HOME': self.base_dir,
            'LANG': 'C.UTF-8',
            'LC_ALL':  'C.UTF-8'
        })
        return self.performer.execute('lxc-attach {env} -n {container_name} -- bash -c "cd {working_dir} && {command}"'.format(
            working_dir=self.working_dir,
            container_name=self.ident,
            command=command.replace('$', '\$').replace('"', '\\"'),
            env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env.items())
        ), logger=logger, writein=writein, max_lines=max_lines)


class LXCMachinesSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def number(self):
        return int(self.data.get('number', 1))

    # TODO rethink
    @property
    def network(self):
        return self.data.get('network', {})

    @property
    def network_ip_start(self):
        return self.network.get('ip_start', 0)

    @property
    def static_network(self):
        return self.network == {} or self.network_ip_start


class LXCMachinesProvider(BaseMachinesProvider):
    settings_class = LXCMachinesSettings
    ip_counter = 0

    def _machine(self, ident, create=False, pub_key=None, ip=None, gateway=None):
        machine = LXCMachine(self.performer, ident=ident)
        created = create and machine.create(
            self.settings.distribution, self.settings.release, ip=ip, gateway=gateway
        )

        machine.start()

        if created:
            #install ssh server
            machine.install_packages('openssh-server')

            #authorize user for ssh
            if pub_key:
                machine.execute('mkdir -p .ssh')
                machine.execute('tee .ssh/authorized_keys', writein=pub_key)

        return machine

    def machines(self, create=False, pub_key=None):
        machines = []

        ip_nums = None
        gateway = None

        if self.settings.static_network:
            for line in self.performer.execute('cat /etc/default/lxc-net').splitlines():
                r = re.match('^LXC_ADDR=\"([\w\.]+)\"$', line)
                if r:
                    gateway = r.group(1)
                    ip_nums = list(map(int, gateway.split('.')))

        for i in range(1, self.settings.number + 1):
            ident = '%s_%000d' % (self.machines_name, i)
            if create:
                if self.settings.network_ip_start:
                    ip = '.'.join(map(str, ip_nums[:3] + [self.settings.network_ip_start + i - 1]))
                elif ip_nums:
                    ip = '.'.join(map(str, ip_nums[:3] + [ip_nums[3] + self.__class__.ip_counter + 1]))
                    self.__class__.ip_counter += 1
                else:
                    ip = None
            else:
                ip = None

            # TODO maybe lxc-clone instead of this - huge performance gain
            machine = self._machine(ident, create=create, pub_key=pub_key, ip=ip, gateway=gateway)
            machines.append(machine)
        return machines

MachinesProvider.register('lxc', LXCMachinesProvider)
