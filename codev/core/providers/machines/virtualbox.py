import re
from base64 import b64encode
from crypt import crypt
from os import urandom, path
from time import sleep

from codev.core.debug import DebugSettings
from codev.core.executor import CommandError
from codev.core.machines import BaseMachine, Machine
from codev.core.providers.executors.ssh import SSHExecutor
from codev.core.settings import BaseSettings
from codev.core.utils import grouper

"""
requirements: wget, isoinfo, mkisofs
archlinux: wget, cdrkit | cdrtools
ubuntu: TODO
"""


class VirtualboxBaseMachineSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data['distribution']

    @property
    def release(self):
        return self.data['release']

    @property
    def username(self):
        return self.data.get('username')

    @property
    def password(self):
        return self.data.get('password')

    @property
    def memory(self):
        return self.data.get('memory', 20000)

    @property
    def hdd(self):
        return self.data.get('hdd', 1024)

    @property
    def share(self):
        return self.data.get('share', {})

    @property
    def iface_lower_ip(self):
        return '192.168.77.101'

    @property
    def iface_upper_ip(self):
        return '192.168.77.200'


class VirtualboxBaseMachine(BaseMachine):
    settings_class = VirtualboxBaseMachineSettings



    @property
    def effective_executor(self):
        return SSHExecutor(settings_data={'hostname': self._ip, 'username': 'root'})

    def exists(self):
        return f'"{self.vm_name}"' in self.executor.execute('VBoxManage list vms').split()

    def is_started(self):
        output = self.executor.execute("VBoxManage list runningvms")
        return bool(re.search(f'^\"{self.vm_name}\"\s+.*', output, re.MULTILINE))

    def start(self):
        self.executor.execute(f'VBoxManage startvm "{self.vm_name}" --type headless')

    def create(self):
        distribution = self.settings.distribution
        release = self.settings.release
        if distribution != 'ubuntu':
            raise RuntimeError(f"Distribution '{distribution}' is not supported")

        # TODO
        # # https://major.io/2015/08/21/understanding-systemds-predictable-network-device-names/
        #
        # # ls /sys/class/net
        # # from lspci
        # if release in ('wily', 'xenial'):
        #     device_1 = 'enp0s3'
        #     device_2 = 'enp0s8'
        # elif release in ('trusty', 'utopic'):
        #     device_1 = 'eth0'
        #     device_2 = 'eth1'
        # else:
        #     raise RuntimeError(f"Release '{release}' is not supported")
        device_1 = 'enp0s3'
        device_2 = 'enp0s8'

        release_iso = self._download_ubuntu_iso(release)

        vm_iso = '/tmp/{ident}.iso'.format(
            release=release,
            ident=self.ident.as_file()
        )

        packages = ['virtualbox-guest-utils', 'openssh-server']

        # TODO packages installation according to runner - ie. ansible require python2

        # FIXME authentication module
        ssh_key = self.executor.execute('ssh-add -L')

        self._prepare_ubuntu_iso(
            release_iso,
            vm_iso,
            self.settings.username,
            self.settings.password,
            self.ident.as_hostname(),
            device_1=device_1,
            device_2=device_2,
            packages=packages,
            ssh_authorized_keys=[ssh_key],
            shares=self.settings.share
        )

        iface_ip = '192.168.77.100'
        dhcp_ip = '192.168.77.100'
        netmask = '255.255.255.0'

        iface = self._create_vbox_iface(iface_ip, dhcp_ip, netmask, self.settings.iface_lower_ip, self.settings.iface_upper_ip)
        self._create_vm(
            ostype='Ubuntu_64',
            memory=self.settings.memory,
            hdd=self.settings.hdd,
            share=self.settings.share,
            hostonly_iface=iface
        )

        self._install_vm(vm_iso)

        while self.is_started():
            sleep(1)

        self._remove_vm_dvd()

        self.executor.execute('rm {vm_iso}'.format(vm_iso=vm_iso))

        self.start()

    @property
    def vm_name(self):
        return self.ident.as_file()

    def _download_ubuntu_iso(self, release, subtype='server', arch='amd64'):
        """

        :param release: It can be version number (17.10) or name (artful)
            because urls http://releases.ubuntu.com/17.10/ and http://releases.ubuntu.com/artful/
            are both valid and have the same content.
        :param subtype:
        :param arch:
        :return:
        """

        def parse_sums_file(fo):
            for iso_checksum in fo:
                r = re.match(iso_file_pattern, iso_checksum)
                if r:
                    iso_file = r.group(1)
                    return iso_file, iso_checksum

            raise Exception() #FIXME

        base_directory = f'~/.cache/codev/{release}/'
        release_base_url = f'http://releases.ubuntu.com/{release}/'
        iso_file_pattern = f'\w+\s+\*(ubuntu-[\d.]+-{subtype}-{arch}.iso)'

        self.executor.create_directory(base_directory)
        with self.executor.change_directory(base_directory):

            # download SHA256SUMS and gpg
            self.executor.execute(f'wget {release_base_url}SHA256SUMS -O SHA256SUMS -o /dev/null')

            with self.executor.open_file('SHA256SUMS') as fo:
                iso_file, iso_checksum = parse_sums_file(fo)

            iso_file_path = path.join(base_directory, iso_file)
            if not self.executor.exists_file(iso_file_path):
                self.executor.execute(f'wget {release_base_url}SHA256SUMS.gpg -O SHA256SUMS.gpg -o /dev/null')

                #FIXME test it
                self.executor.execute('gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys "8439 38DF 228D 22F7 B374 2BC0 D94A A3F0 EFE2 1092" "C598 6B4F 1257 FFA8 6632 CBA7 4618 1433 FBB7 5451"')
                self.executor.execute('gpg --list-keys --with-fingerprint 0xFBB75451 0xEFE21092')
                self.executor.execute('gpg --verify SHA256SUMS.gpg SHA256SUMS')

                self.executor.execute(f'wget {release_base_url}{iso_file} -O {iso_file} -o /dev/null')

                self.executor.execute('sha256sum -c', writein=iso_checksum)

        return iso_file_path

    def _extract_iso(self, source_iso, target_dir):
        actual_directory = '/'
        for line in self.executor.execute(f'isoinfo -R -l -i {source_iso}').splitlines():
            r = re.match('^Directory\slisting\sof\s(.*)$', line)
            if r:
                actual_directory = r.group(1)
                self.executor.create_directory(f'{target_dir}{actual_directory}')
            else:
                r = re.match('^-.*\]\s+(.*)', line)
                if r:
                    filename = r.group(1)
                    self.executor.execute(
                        f'isoinfo -R -i {source_iso} -x {actual_directory}{filename} > {target_dir}{actual_directory}{filename}'
                    )
                    continue

                r = re.match('^l.*\]\s+(.*)\s->\s(.*)', line)
                if r:
                    symlink = r.group(1)
                    target = r.group(2)

                    self.executor.execute(
                        f'cd {target_dir}{actual_directory} && ln -s {target} {symlink}'
                    )

    def _prepare_ubuntu_iso(
        self, source_iso, target_iso, username, password, hostname,
        ip='', gateway='', nameserver='', device_1='enp0s3', device_2='enp0s8',
        packages=None, ssh_authorized_keys=None, shares={}
    ):

        if packages is None:
            packages = []
        # http://serverfault.com/questions/378529/linux-kickstart-scipts
        sandbox = '/tmp/ks_iso'
        dir_path = path.dirname(__file__)
        template_path = f'{dir_path}/ubuntu_template'

        if not DebugSettings.preserve_cache or not self.executor.exists_directory(sandbox):
            # cleanup
            self.executor.delete_path(sandbox)

            # make a sandbox
            self.executor.create_directory(sandbox)

            # 7z neextrahuje symlinky a dlouhe soubory, mount potrebuje root prava
            self._extract_iso(source_iso, sandbox)

        # copy late_command template to target iso dir
        with open(f'{sandbox}/late_command.sh', 'w+') as late_command:
            for line in open(f'{template_path}/late_command.sh'):
                late_command.write(
                    line.format(
                        username=username,
                        ssh_authorized_keys='\n'.join(ssh_authorized_keys),
                        fstab='\n'.join([
                            f"echo \"{share_name} `getent passwd \\\"{username}\\\" | cut -d: -f6`/{share_name} vboxsf rw,uid=`id {username} -u`,gid=`id {username} -u` 0 0\" >> /etc/fstab"
                            for share_name, share_directory in shares.items()
                        ]),
                        device_2=device_2
                    )
                )
        self.executor.execute(f'chmod +x {template_path}/late_command.sh')

        with open(f'{sandbox}/preseed.cfg', 'w+') as file_seed:
            encrypted_password = crypt(
                password, '$6${salt}'.format(
                    salt=b64encode(urandom(6)).decode()
                )
            )
            for line in open(f'{template_path}/preseed.cfg'):
                file_seed.write(
                    line.format(
                        fstype='ext4',
                        username=username,
                        encrypted_password=encrypted_password,
                        ip=ip,
                        gateway=gateway,
                        nameserver=nameserver,
                        device_1=device_1,
                        packages=' '.join(packages),
                        hostname=hostname
                    )
                )

        for filepath in ('isolinux.cfg', 'langlist', 'txt.cfg'):
            self.executor.send_file(f'{template_path}/isolinux/{filepath}', f'{sandbox}/isolinux/{filepath}')

        self.executor.execute(
            f'mkisofs -D -r -V "ubuntu" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {target_iso} {sandbox}'
        )

        if not DebugSettings.preserve_cache:
            # cleanup
            self.executor.delete_path(sandbox)

    def _create_vbox_iface(self, ip, dhcp_ip, netmask, lower_ip, upper_ip):
        """
        Create hostonly network interface

        :param ip: IP address of interface
        :return: str
        """
        output = self.executor.execute('VBoxManage list hostonlyifs')

        iface = None
        for line in output.splitlines():
            r = re.match('^Name:\s+(.*)$', line)
            if r:
                iface = r.group(1)

            regex = '^IPAddress:\s+{ip}$'.format(ip=ip.replace('.', '\.'))
            r = re.match(regex, line)
            if r:
                break
        else:
            output = self.executor.execute('VBoxManage hostonlyif create')
            r = re.search("Interface\s\'(\w+)\'\swas\ssuccessfully\screated", output, re.S)
            if r:
                iface = r.group(1)
                self.executor.execute('VBoxManage hostonlyif ipconfig {iface} --ip {ip}'.format(iface=iface, ip=ip))
                self.executor.execute(
                    f'VBoxManage dhcpserver add --ifname {iface} --ip {dhcp_ip} --netmask {netmask} --lowerip {lower_ip} --upperip {upper_ip} --enable'
                )

        if not iface:
            raise RuntimeError('Error during creating virtualbox network host-only interface.')
        return iface

    def _create_vm(self, ostype, hdd, memory, share, hostonly_iface):
        # create VM
        self.executor.execute(
            f'VBoxManage createvm --name "{self.vm_name}" --ostype "{ostype}" --register'
        )

        # setup VM + ifaces
        self.executor.execute(
            f'VBoxManage modifyvm "{self.vm_name}" --memory {memory} --acpi on --vram 16 --boot1 dvd --nic1 nat --nictype1 Am79C973 --nic2 hostonly --nictype2 Am79C970A --hostonlyadapter2 {hostonly_iface}'
        )

        hdd_dir = '~/.share/codev/virtualbox'
        medium = '{hdd_dir}/{ident}.vdi'.format(
            ident=self.ident.as_file(),
            hdd_dir=hdd_dir
        )
        # create storage

        if self.executor.exists_file(medium):
            self.executor.delete_path(medium)

        self.executor.execute(
            f'VBoxManage createhd --filename {medium} --size {hdd}'
        )
        # if error appears, delete {name}.vdi and "runvboxmanage closemedium disk {name}.vdi"

        # create SATA
        self.executor.execute(f'VBoxManage storagectl "{self.vm_name}" --name "SATA" --add sata --portcount 1')

        # create IDE
        self.executor.execute(f'VBoxManage storagectl "{self.vm_name}" --name "IDE" --add ide')

        # attach storage to SATA
        self.executor.execute(
            f'VBoxManage storageattach "{self.vm_name}" --storagectl "SATA" --port 0 --device 0 --type hdd --medium {medium}'
        )

        #create shared points
        for share_name, share_directory in share.items():
            self.executor.execute(
                f'VBoxManage sharedfolder add "{self.vm_name}" --name "{share_name}" --hostpath "{share_directory}"'
            )

    def _install_vm(self, install_iso):
        # attach install iso
        self.executor.execute(
            f'VBoxManage storageattach "{self.vm_name}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium {install_iso}'
        )

        # install
        self.start()

    def _remove_vm_dvd(self):
        # remove install iso
        while not self.executor.check_execute(
                f'VBoxManage storageattach "{self.vm_name}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium none'
        ):
            sleep(1)

    @property
    def _ip(self):
        for i in range(20):
            value_ip = self.executor.execute(
                f'VBoxManage guestproperty get "{self.vm_name}" "/VirtualBox/GuestInfo/Net/1/V4/IP"'
            )
            if value_ip == 'No value set!':
                sleep(3)
                continue
            else:
                return value_ip.split()[1]
        
        # TODO raise exception?
        return None


class VirtualboxMachine(Machine, VirtualboxBaseMachine):
    provider_name = 'virtualbox'

    @property
    def ip(self):
        return self._ip
