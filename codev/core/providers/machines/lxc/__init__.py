from uuid import uuid1

import re
from time import sleep
from contextlib import contextmanager
from logging import getLogger
from os import path

from codev.core.settings import BaseSettings
from codev.core.machines import MachinesProvider, BaseMachine
from codev.core.executor import BackgroundExecutor, CommandError, CommandError

logger = getLogger(__name__)

class LXCBaseMachine(BaseMachine):
    def exists(self):
        try:
            output = self.executor.execute('lxc-ls')
        except CommandError:
            # lxc is not installed so there is no machine
            return False
        return self.ident in output.split()

    def started(self):
        output = self.executor.execute('lxc-info -n {container_name} -s'.format(
            container_name=self.ident,
        ))

        r = re.match('^State:\s+(.*)$', output.strip())
        if r:
            state = r.group(1)
        else:
            # TODO
            raise ValueError('o:%s:o' % output)

        if state == 'RUNNING':
            if self.ip and self.check_execute('runlevel'):
                return True
            else:
                return False
        elif state == 'STOPPED':
            return False
        else:
            # TODO
            raise ValueError('s:%s:s' % state)

    def create(self, settings, ssh_key=None): #, ip=None, gateway=None):
        distribution = settings.distribution
        release = settings.release
        architecture = self._get_architecture()
        if not self.executor.check_execute(
            'lxc-create -t {distribution} -n {container_name} -- --release {release}'.format(
                container_name=self.ident,
                distribution=distribution,
                release=release,
                architecture=architecture
            )
        ):
            self.executor.execute('lxc-create -t download -n {container_name} -- --dist {distribution} --release {release} --arch {architecture}'.format(
                container_name=self.ident,
                distribution=distribution,
                release=release,
                architecture=architecture
            ))
        self._configure()  # ip=ip, gateway=gateway)

        self.start()

        # install ssh server
        self.install_packages('openssh-server')

        # authorize user for ssh
        if ssh_key:
            self.execute('mkdir -p .ssh')
            self.execute('tee .ssh/authorized_keys', writein=ssh_key)

    def start(self):
        self.executor.execute('lxc-start -n {container_name}'.format(
            container_name=self.ident,
        ))
        #TODO timeout
        while not self.is_started():
            sleep(0.5)

        return True

    def stop(self):
        self.executor.execute('lxc-stop -n {container_name}'.format(
            container_name=self.ident,
        ))


class LXCMachine(LXCBaseMachine):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__container_directory = None
        self.__share_directory = None
        self.__gateway = None
        self.base_dir = '/root'



    def destroy(self):
        self.executor.execute('rm -rf {share_directory}'.format(share_directory=self.share_directory))
        self.executor.execute('lxc-destroy -n {container_name}'.format(
            container_name=self.ident,
        ))

    def _get_architecture(self):
        architecture = self.executor.execute('uname -m')
        if architecture == 'x86_64':
            architecture = 'amd64'
        return architecture

    def _configure(self, ip=None, gateway=None):
        self.executor.execute('mkdir -p {share_directory} && chmod 7777 {share_directory}'.format(
            share_directory=self.share_directory
        ))
        if self.executor.check_execute('[ -f /usr/share/lxc/config/nesting.conf ]'):
            nesting = 'lxc.mount.auto = cgroup\nlxc.include = /usr/share/lxc/config/nesting.conf'
        else:
            nesting = 'lxc.mount.auto = cgroup\nlxc.aa_profile = lxc-container-default-with-nesting'

        if ip:
            template_dir = 'static'
            self.executor.send_file(
                '{directory}/templates/{template_dir}/network_interfaces'.format(
                    directory=path.dirname(__file__),
                    template_dir=template_dir
                ),
                '{container_root}/etc/network/interfaces'.format(
                    container_root=self.container_root
                )
            )
            self.executor.execute(
                'rm -f {container_root}/etc/resolv.conf'.format(
                    container_root=self.container_root
                )
            )
            self.executor.execute(
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
            self.executor.execute('echo "{line}" >> {container_config}'.format(
                    line=line.format(
                        ip=ip,
                        share_directory=self.share_directory,
                        nesting=nesting
                    ),
                    container_config=self.container_config
                )
            )

        # ubuntu trusty workaround
        # self.executor.execute("sed -e '/lxc.include\s=\s\/usr\/share\/lxc\/config\/ubuntu.userns\.conf/ s/^#*/#/' -i {container_config}".format(container_config=self.container_config))

    @property
    def share_directory(self):
        if not self.__share_directory:
            # abs_base_dir = self.executor.execute('pwd')
            abs_base_dir = '$HOME/.local/codev'
            return '{abs_base_dir}/{container_name}/share'.format(
                abs_base_dir=abs_base_dir,
                container_name=self.ident
            )
        return self.__share_directory

    @property
    def _container_directory(self):
        if not self.__container_directory:
            lxc_path = self.executor.execute('lxc-config lxc.lxcpath')
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



    @property
    def ip(self):
        output = self.executor.execute('lxc-info -n {container_name} -i'.format(
            container_name=self.ident,
        ))

        for line in output.splitlines():
            r = re.match('^IP:\s+([0-9\.]+)$', line)
            if r:
                return r.group(1)

        return None

    @property
    def _gateway(self):
        if not self.__gateway:
            # attempts to get gateway ip
            for i in range(3):
                self.__gateway = self.executor.execute(
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

        self.executor.execute('lxc-usernsexec -- cp {container_root}{remote_path} {tempfile}'.format(
            tempfile=tempfile,
            remote_path=remote_path,
            container_root=self.container_root
        ))
        try:
            with self.executor.get_fo(tempfile) as fo:
                yield fo
        finally:
            self.executor.execute('lxc-usernsexec -- rm {tempfile}'.format(tempfile=tempfile))

    def send_file(self, source, target):
        tempfile = '/tmp/{filename}.tmp'.format(filename=uuid1())
        self.executor.send_file(source, tempfile)
        target = self._sanitize_path(target)

        self.executor.execute('lxc-usernsexec -- cp {tempfile} {container_root}{target}'.format(
            tempfile=tempfile,
            target=target,
            container_root=self.container_root
        ))
        self.executor.execute('rm {tempfile}'.format(tempfile=tempfile))

    def execute(self, command, env=None, logger=None, writein=None):
        if env is None:
            env = {}
        env.update({
            'HOME': '/root',
            'LANG': 'C.UTF-8',
            'LC_ALL':  'C.UTF-8'
        })

        with self.executor.change_directory(self.working_dir):
            return self.executor.execute_wrapper(
                'lxc-attach {env} -n {container_name} -- {{command}}'.format(
                    container_name=self.ident,
                    env=' '.join('-v {var}={value}'.format(var=var, value=value) for var, value in env.items())
                ),
                command,
                logger=logger,
                writein=writein
            )

    def share(self, source, target, bidirectional=False):
        share_target = '{share_directory}/{target}'.format(
            share_directory=self.share_directory,
            target=target
        )

        # copy all files to share directory
        # sequence /. just after source paramater makes cp command idempotent
        self.executor.execute(
            'cp -Ru {source}/. {share_target}'.format(
                source=source,
                share_target=share_target
            )
        )

        if bidirectional:
            self.executor.execute(
                'chmod -R go+w {share_target}'.format(
                    share_target=share_target
                )
            )

        source_target_background_runner = BackgroundExecutor(
            executor=self.executor, ident='share_{ident}'.format(
                ident=self.ident
            )
        )
        dir_path = path.dirname(__file__)

        # prevent sync loop - if there is no change in file don't sync
        # This option may eat a lot of memory on huge file trees. see 'man clsync'
        modification_signature = ' --modification-signature "*"' if bidirectional else ''

        # TODO keep in mind relative and abs paths
        try:
            source_target_background_runner.execute(
                'TO={share_target}'
                ' clsync'
                ' --label live'
                ' --mode rsyncshell'
                ' --delay-sync 2'
                ' --delay-collect 3'
                ' --watch-dir {source}'
                '{modification_signature}'
                ' --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(
                    modification_signature=modification_signature,
                    share_target=share_target,
                    source=source,
                    dir_path=dir_path
                ),
                wait=False
            )
        except CommandError:
            pass

        if bidirectional:
            target_source_background_runner = BackgroundExecutor(
                executor=self.executor, ident='share_back_{ident}'.format(
                    ident=self.ident
                )
            )
            try:
                target_source_background_runner.execute(
                    'TO={source}'
                    ' clsync'
                    ' --label live'
                    ' --mode rsyncshell'
                    ' --delay-sync 2'
                    ' --delay-collect 3'
                    ' --watch-dir {share_target}'
                    ' --modification-signature "*"'
                    ' --sync-handler {dir_path}/scripts/clsync-synchandler-rsyncshell.sh'.format(
                        share_target=share_target,
                        source=source,
                        dir_path=dir_path
                    ),
                    wait=False
                )
            except CommandError:
                pass

        if not self.check_execute('[ -L {target} ]'.format(target=target)):
            self.execute(
                'ln -s /share/{target} {target}'.format(
                    target=target,
                )
            )


class LXCMachinesSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data['distribution']

    @property
    def release(self):
        return self.data['release']

    @property
    def number(self):
        return int(self.data.get('number', 1))


class LXCMachinesProvider(MachinesProvider):
    provider_name = 'lxc'
    settings_class = LXCMachinesSettings
    machine_class = LXCMachine
