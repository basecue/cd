import re
from os import urandom, path
from crypt import crypt
from base64 import b64encode
from time import sleep

from codev.core.settings import BaseSettings
from codev.core.machines import BaseMachine, Machine
from codev.core.executor import Executor


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


class VirtualboxBaseMachine(BaseMachine):
    settings_class = VirtualboxBaseMachineSettings

    @property
    def executor(self):
        return Executor(
            'ssh', settings_data={'hostname': self._ip, 'username': 'root'}
        )

    def exists(self):
        return '"{vm_name}"'.format(vm_name=self.vm_name) in self.inherited_executor.execute('VBoxManage list vms').split()

    def is_started(self):
        output = self.inherited_executor.execute("VBoxManage list runningvms")
        return bool(re.search('^\"{vm_name}\"\s+.*'.format(vm_name=self.vm_name), output, re.MULTILINE))

    def start(self):
        self.inherited_executor.execute('VBoxManage startvm "{vm_name}" --type headless'.format(vm_name=self.vm_name))

    def create(self):
        distribution = self.settings.distribution
        release = self.settings.release
        if distribution != 'ubuntu':
            raise RuntimeError("Distribution '{distribution}' is not supported".format(distribution=distribution))
        if release in ('wily', 'xenial'):
            device_1 = 'enp0s3'
            device_2 = 'enp0s8'
        elif release in ('trusty', 'utopic'):
            device_1 = 'eth0'
            device_2 = 'eth1'
        else:
            raise RuntimeError("Release '{release}' is not supported".format(release=release))

        release_iso = self._download_ubuntu_iso(release)

        vm_iso = '/tmp/{ident}.iso'.format(
            release=release,
            ident=self.ident.as_file()
        )

        packages = ['virtualbox-guest-utils', 'openssh-server']

        # TODO packages installation according to runner - ie. ansible require python2

        # FIXME authentication module
        ssh_key = self.inherited_executor.execute('ssh-add -L')

        self._prepare_ubuntu_iso(
            release_iso, vm_iso,
            self.settings.username, self.settings.password, self.ident.as_hostname(),
            device_1=device_1, device_2=device_2,
            packages=packages, ssh_authorized_keys=[ssh_key]
        )

        iface_ip = '192.168.77.100'
        dhcp_ip = '192.168.77.100'
        netmask = '255.255.255.0'
        lower_ip = '192.168.77.100'
        upper_ip = '192.168.77.200'
        iface = self._create_vbox_iface(iface_ip, dhcp_ip, netmask, lower_ip, upper_ip)
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

        try:
            self._remove_vm_dvd()
        except:
            pass
        else:
            self.inherited_executor.execute('rm {vm_iso}'.format(vm_iso=vm_iso))

        self.start()

    @property
    def vm_name(self):
        return self.ident.as_file()

    def _download_ubuntu_iso(self, release, subtype='server', arch='amd64'):
        # FIXME generalize

        def parse_sums_file(fo):
            for iso_checksum in fo:
                r = re.match(iso_file_pattern, iso_checksum)
                if r:
                    iso_file = r.group(1)
                    return iso_file, iso_checksum

            raise Exception() #FIXME

        release_to_number = {
            'trusty': '14.04',
            'wily': '15.10',
            'xenial': '16.04'
        }

        release_number = release_to_number[release]
        base_directory = '~/.cache/codev/{release_number}/'.format(release_number=release_number)
        release_base_url = 'http://releases.ubuntu.com/{release_number}/'.format(release_number=release_number)
        iso_file_pattern = '\w+\s+\*(ubuntu-[\d.]+-{subtype}-{arch}.iso)'.format(subtype=subtype, arch=arch)

        self.inherited_executor.create_directory(base_directory)
        with self.inherited_executor.change_directory(base_directory):

            # download SHA256SUMS and gpg
            self.inherited_executor.execute('wget {release_base_url}SHA256SUMS -o /dev/null'.format(release_base_url=release_base_url))

            with self.inherited_executor.get_fo('SHA256SUMS') as fo:
                iso_file, iso_checksum = parse_sums_file(fo)

            iso_file_path = path.join(base_directory, iso_file)
            if not self.inherited_executor.exists_file(iso_file_path):
                self.inherited_executor.execute('wget {release_base_url}SHA256SUMS.gpg -o /dev/null'.format(release_base_url=release_base_url))

                #FIXME test it
                self.inherited_executor.execute('gpg --keyserver hkp://keyserver.ubuntu.com --recv-keys "8439 38DF 228D 22F7 B374 2BC0 D94A A3F0 EFE2 1092" "C598 6B4F 1257 FFA8 6632 CBA7 4618 1433 FBB7 5451"')
                self.inherited_executor.execute('gpg --list-keys --with-fingerprint 0xFBB75451 0xEFE21092')
                self.inherited_executor.execute('gpg --verify SHA256SUMS.gpg SHA256SUMS')

                self.inherited_executor.execute(
                    'wget {release_base_url}{iso_file} -o /dev/null'.format(
                        release_base_url=release_base_url,
                        iso_file=iso_file
                    )
                )

                self.inherited_executor.execute('sha256sum -c', writein=iso_checksum)

        return iso_file_path

    def _extract_iso(self, source_iso, target_dir):
        actual_directory = '/'
        for line in self.inherited_executor.execute('isoinfo -R -l -i {source_iso}'.format(source_iso=source_iso)).splitlines():
            r = re.match('^Directory\slisting\sof\s(.*)$', line)
            if r:
                actual_directory = r.group(1)
                self.inherited_executor.create_directory(
                    '{target_dir}{actual_directory}'.format(
                        target_dir=target_dir,
                        actual_directory=actual_directory
                    )
                )
            else:
                r = re.match('^-.*\]\s+(.*)', line)
                if r:
                    filename = r.group(1)
                    self.inherited_executor.execute(
                        'isoinfo -R -i {source_iso} -x {actual_directory}{filename} > {target_dir}{actual_directory}{filename}'.format(
                            target_dir=target_dir,
                            actual_directory=actual_directory,
                            source_iso=source_iso,
                            filename=filename
                        )
                    )
                    continue

                r = re.match('^l.*\]\s+(.*)\s->\s(.*)', line)
                if r:
                    symlink = r.group(1)
                    target = r.group(2)

                    self.inherited_executor.execute(
                        'cd {target_dir}{actual_directory} && ln -s {target} {symlink}'.format(
                            target_dir=target_dir,
                            actual_directory=actual_directory,
                            target=target,
                            symlink=symlink
                        )
                    )

    def _prepare_ubuntu_iso(
        self, source_iso, target_iso, username, password, hostname,
        ip='', gateway='', nameserver='', device_1='enp0s3', device_2='enp0s8',
        packages=None, ssh_authorized_keys=None
    ):

        if packages is None:
            packages = []
        # http://serverfault.com/questions/378529/linux-kickstart-scipts
        sandbox = '/tmp/ks_iso'
        dir_path = path.dirname(__file__)
        template_path = '{dir_path}/ubuntu_template'.format(dir_path=dir_path)
        # cleanup
        self.inherited_executor.execute(
            'rm -rf {sandbox}'.format(
                sandbox=sandbox
            )
        )

        # make a sandbox
        self.inherited_executor.create_directory(sandbox)

        # 7z neextrahuje symlinky a dlouhe soubory, mount potrebuje root prava
        self._extract_iso(source_iso, sandbox)

        # copy kickstart templates to target iso dir
        with open(
                '{sandbox}/ks.cfg'.format(
                    sandbox=sandbox
                ),
                'w+'
        ) as file_ks:
            encrypted_password = crypt(
                password, '$6${salt}'.format(
                    salt=b64encode(urandom(6)).decode()
                )
            )
            for line in open('{template_path}/ks.cfg'.format(template_path=template_path)):
                file_ks.write(
                    line.format(
                        fstype='btrfs',
                        username=username,
                        encrypted_password=encrypted_password,
                        ip=ip,
                        gateway=gateway,
                        nameserver=nameserver,
                        device_1=device_1,
                        device_2=device_2,
                        packages='\n'.join(packages),
                        post_nochroot='',
                        post='echo "{username} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers'.format(username=username),
                        ssh_authorized_keys='\n'.join(ssh_authorized_keys),
                        hostname=hostname
                    )
                )

        for filepath in ('isolinux.cfg', 'langlist', 'txt.cfg'):
            self.inherited_executor.send_file(
                '{template_path}/isolinux/{filepath}'.format(template_path=template_path, filepath=filepath),
                '{sandbox}/isolinux/{filepath}'.format(sandbox=sandbox, filepath=filepath)
            )

        self.inherited_executor.execute(
            'mkisofs -D -r -V "ubuntu" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {target_iso} {sandbox}'.format(
                target_iso=target_iso,
                sandbox=sandbox
            )
        )

        # cleanup
        self.inherited_executor.execute(
            'rm -rf {sandbox}'.format(
                sandbox=sandbox
            )
        )

    def _create_vbox_iface(self, ip, dhcp_ip, netmask, lower_ip, upper_ip):
        """
        Create hostonly network interface

        :param ip: IP address of interface
        :return: str
        """
        output = self.inherited_executor.execute('VBoxManage list hostonlyifs')

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
            output = self.inherited_executor.execute('VBoxManage hostonlyif create')
            r = re.search("Interface\s\'(\w+)\'\swas\ssuccessfully\screated", output, re.S)
            if r:
                iface = r.group(1)
                self.inherited_executor.execute('VBoxManage hostonlyif ipconfig {iface} --ip {ip}'.format(iface=iface, ip=ip))
                self.inherited_executor.execute(
                    'VBoxManage dhcpserver add --ifname {iface} --ip {dhcp_ip} --netmask {netmask} --lowerip {lower_ip} --upperip {upper_ip} --enable'.format(
                        iface=iface,
                        dhcp_ip=dhcp_ip,
                        netmask=netmask,
                        lower_ip=lower_ip,
                        upper_ip=upper_ip
                    )
                )

        if not iface:
            raise RuntimeError('Error during creating virtualbox network host-only interface.')
        return iface

    def _create_vm(self, ostype, hdd, memory, share, hostonly_iface):
        # create VM
        self.inherited_executor.execute(
            'VBoxManage createvm --name "{vm_name}" --ostype "{ostype}" --register'.format(
                vm_name=self.vm_name, ostype=ostype
            )
        )

        # setup VM + ifaces
        self.inherited_executor.execute(
            'VBoxManage modifyvm "{vm_name}" --memory {memory} --acpi on --vram 16 --boot1 dvd --nic1 nat --nictype1 Am79C973 --nic2 hostonly --nictype2 Am79C970A --hostonlyadapter2 {hostonly_iface}'.format(
                vm_name=self.vm_name,
                memory=memory,
                hostonly_iface=hostonly_iface
            )
        )

        hdd_dir = '.share/codev/virtualbox'
        medium = '{hdd_dir}/{ident}.vdi'.format(
            ident=self.ident.as_file(),
            hdd_dir=hdd_dir
        )
        # create storage
        self.inherited_executor.execute(
            'VBoxManage createhd --filename {medium} --size {hdd}'.format(
                medium=medium, hdd=hdd
            )
        )
        # if error appears, delete {name}.vdi and "runvboxmanage closemedium disk {name}.vdi"

        # create SATA
        self.inherited_executor.execute('VBoxManage storagectl "{vm_name}" --name "SATA" --add sata --portcount 1'.format(vm_name=self.vm_name))

        # create IDE
        self.inherited_executor.execute('VBoxManage storagectl "{vm_name}" --name "IDE" --add ide'.format(vm_name=self.vm_name))

        # attach storage to SATA
        self.inherited_executor.execute(
            'VBoxManage storageattach "{vm_name}" --storagectl "SATA" --port 0 --device 0 --type hdd --medium {medium}'.format(
                vm_name=self.vm_name,
                medium=medium
            )
        )

        #create shared points
        for share_name, share_directory in share.items():
            self.inherited_executor.execute(
                'VBoxManage sharedfolder add "{vm_name}" --name "{share_name}" --hostpath "{share_directory}"'.format(
                    vm_name=self.vm_name,
                    share_name=share_name,
                    share_directory=share_directory
                )
            )

    def _install_vm(self, install_iso):
        # attach install iso
        self.inherited_executor.execute(
            'VBoxManage storageattach "{vm_name}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium {iso}'.format(
                vm_name=self.vm_name, iso=install_iso
            )
        )

        # install
        self.start()

    def _remove_vm_dvd(self):
        # remove install iso
        self.inherited_executor.execute(
            'VBoxManage storageattach "{vm_name}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium none'.format(
                vm_name=self.vm_name
            )
        )

    @property
    def _ip(self):
        for i in range(20):
            value_ip = self.inherited_executor.execute(
                'VBoxManage guestproperty get "{vm_name}" "/VirtualBox/GuestInfo/Net/1/V4/IP"'.format(
                    vm_name=self.vm_name
                )
            )
            if value_ip == 'No value set!':
                sleep(3)
                continue
            else:
                return value_ip.split()[1]
        return None
        # raise Exception(
        #     "Guest additions are not installed for virtualbox machine '{ident}'.".format(
        #         ident=self.ident
        #     )
        # )


class VirtualboxMachine(Machine, VirtualboxBaseMachine):
    provider_name = 'virtualbox'

    @property
    def ip(self):
        return self._ip
