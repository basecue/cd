from codev.settings import BaseSettings
from codev.machines import MachinesProvider, BaseMachine
from codev.performer import Performer
import re
from os import urandom, path
from crypt import crypt
from base64 import b64encode
from time import sleep


"""
requirements: wget, isoinfo, mkisofs
archlinux: cdrkit | cdrtools
ubuntu: TODO
"""


class VirtualboxMachine(BaseMachine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def exists(self):
        return self.ident in self.performer.execute('VBoxManage list vms')

    def is_started(self):
        output = self.performer.execute("VBoxManage list runningvms")
        return bool(re.search('^\"{ident}\"\s+.*'.format(ident=self.ident), output, re.MULTILINE))

    def start(self):
        self.performer.execute('VBoxManage startvm "{ident}"'.format(ident=self.ident))

    def create(self, distribution, release, install_ssh_server=False, ssh_key=None):
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
            ident=self.ident
        )

        packages = ['virtualbox-guest-utils']
        if install_ssh_server:
            packages.append('openssh-server')

        self._prepare_ubuntu_iso(
            release_iso, vm_iso,
            'codev', 'codev', self.ident.replace('_', '-'),
            device_1=device_1, device_2=device_2,
            packages=packages, ssh_authorized_keys=[ssh_key]
        )

        iface_ip = '192.168.77.100'
        dhcp_ip = '192.168.77.100'
        netmask = '255.255.255.0'
        lower_ip = '192.168.77.100'
        upper_ip = '192.168.77.200'
        iface = self._create_vbox_iface(iface_ip, dhcp_ip, netmask, lower_ip, upper_ip)
        self._create_vm(hostonly_iface=iface)

        self._install_vm(vm_iso)

        while self.is_started():
            sleep(1)

        try:
            self._remove_vm_dvd()
        except:
            pass
        else:
            self.performer.execute('rm {vm_iso}'.format(vm_iso=vm_iso))

        self.start()

    def execute(self, command, logger=None, writein=None, max_lines=None, **kwargs):
        return Performer('ssh', settings_data={'hostname': self.ip, 'username': 'root'}).execute(
            command, logger=logger, writein=writein, max_lines=max_lines
        )
        # return super().execute(
        #     'ssh root@{ip} -- {command}'.format(
        #         ip=self.ip, command=command, logger=logger, writein=writein, max_lines=max_lines
        #     )
        # )

    def destroy(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def _download_ubuntu_iso(self, release, subtype='server', arch='amd64'):
        release_to_number = {
            'trusty': '14.04.3',
            'wily': '15.10',
            'xenial': '16.04'
        }

        release_number = release_to_number[release]

        release_iso = '~/.cache/codev/ubuntu.{release}.iso'.format(release=release)
        if not self.performer.check_execute('[ -f {release_iso} ]'.format(release_iso=release_iso)):
            self.performer.execute('mkdir -p ~/.cache/codev/')
            self.performer.execute(
                'wget http://releases.ubuntu.com/{release_dir}/ubuntu-{release_number}-{subtype}-{arch}.iso -O {release_iso} -o /dev/null'.format(
                    release_dir='.'.join(release_number.split('.')[:2]),
                    release_number=release_number,
                    subtype=subtype,
                    arch=arch,
                    release_iso=release_iso
                )
            )
            # TODO check checksum and move file to release_iso, else delete it and raise exception
        return release_iso

    def _extract_iso(self, source_iso, target_dir):
        actual_directory = '/'
        for line in self.performer.execute('isoinfo -R -l -i {source_iso}'.format(source_iso=source_iso)).splitlines():
            r = re.match('^Directory\slisting\sof\s(.*)$', line)
            if r:
                actual_directory = r.group(1)
                self.performer.execute(
                    'mkdir -p {target_dir}{actual_directory}'.format(
                        target_dir=target_dir,
                        actual_directory=actual_directory
                    )
                )
            else:
                r = re.match('^-.*\]\s+(.*)', line)
                if r:
                    filename = r.group(1)
                    self.performer.execute(
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

                    self.performer.execute(
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
        packages=None, ssh_private_key='', ssh_public_key='', ssh_authorized_keys=None
    ):

        if packages is None:
            packages = []
        # http://serverfault.com/questions/378529/linux-kickstart-scipts
        sandbox = '/tmp/ks_iso'
        dir_path = path.dirname(__file__)
        template_path = '{dir_path}/ubuntu_template'.format(dir_path=dir_path)
        # cleanup
        self.performer.execute(
            'rm -rf {sandbox}'.format(
                sandbox=sandbox
            )
        )

        # make a sandbox
        self.performer.execute('mkdir -p {sandbox}'.format(sandbox=sandbox))

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
                        ssh_private_key=ssh_private_key,
                        ssh_public_key=ssh_public_key,
                        ssh_authorized_keys='\n'.join(ssh_authorized_keys),
                        hostname=hostname
                    )
                )

        for filepath in ('isolinux.cfg', 'langlist', 'txt.cfg'):
            self.performer.send_file(
                '{template_path}/isolinux/{filepath}'.format(template_path=template_path, filepath=filepath),
                '{sandbox}/isolinux/{filepath}'.format(sandbox=sandbox, filepath=filepath)
            )

        self.performer.execute(
            'mkisofs -D -r -V "ubuntu" -cache-inodes -J -l -b isolinux/isolinux.bin -c isolinux/boot.cat -no-emul-boot -boot-load-size 4 -boot-info-table -o {target_iso} {sandbox}'.format(
                target_iso=target_iso,
                sandbox=sandbox
            )
        )

        # cleanup
        self.performer.execute(
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
        output = self.performer.execute('VBoxManage list hostonlyifs')

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
            output = self.performer.execute('VBoxManage hostonlyif create')
            r = re.search("Interface\s\'(\w+)\'\swas\ssuccessfully\screated", output, re.S)
            if r:
                iface = r.group(1)
                self.performer.execute('VBoxManage hostonlyif ipconfig {iface} --ip {ip}'.format(iface=iface, ip=ip))
                self.performer.execute(
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

    def _create_vm(self, ostype='Ubuntu_64', hdd=20000, memory=1024, hostonly_iface=''):
        # create VM
        self.performer.execute('VBoxManage createvm --name "{ident}" --ostype "Ubuntu_64" --register'.format(ident=self.ident))

        # setup VM + ifaces
        self.performer.execute(
            'VBoxManage modifyvm "{ident}" --memory {memory} --acpi on --vram 10 --boot1 dvd --nic1 nat --nictype1 Am79C973 --nic2 hostonly --nictype2 Am79C970A --hostonlyadapter2 {hostonly_iface}'.format(
                ident=self.ident,
                memory=memory,
                hostonly_iface=hostonly_iface
            )
        )

        hdd_dir = '.share/codev/virtualbox'
        medium = '{hdd_dir}/{ident}.vdi'.format(
            ident=self.ident,
            hdd_dir=hdd_dir
        )
        # create storage
        self.performer.execute(
            'VBoxManage createhd --filename {medium} --size {hdd}'.format(
                ident=self.ident, medium=medium, hdd=hdd
            )
        )
        # if error appears, delete {name}.vdi and "runvboxmanage closemedium disk {name}.vdi"

        # create SATA
        self.performer.execute('VBoxManage storagectl "{ident}" --name "SATA" --add sata'.format(ident=self.ident))

        # create IDE
        self.performer.execute('VBoxManage storagectl "{ident}" --name "IDE" --add ide'.format(ident=self.ident))

        # attach storage to SATA
        self.performer.execute(
            'VBoxManage storageattach "{ident}" --storagectl "SATA" --port 0 --device 0 --type hdd --medium {medium}'.format(
                ident=self.ident,
                medium=medium
            )
        )

    def _install_vm(self, install_iso):
        # attach install iso
        self.performer.execute(
            'VBoxManage storageattach "{ident}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium {iso}'.format(
                ident=self.ident, iso=install_iso
            )
        )

        # install
        self.start()

    def _remove_vm_dvd(self):
        # remove install iso
        self.performer.execute(
            'VBoxManage storageattach "{ident}" --storagectl "IDE" --port 1 --device 0 --type dvddrive --medium none'.format(
                ident=self.ident
            )
        )

    @property
    def ip(self):
        for i in range(20):
            value_ip = self.performer.execute(
                'VBoxManage guestproperty get "{ident}" "/VirtualBox/GuestInfo/Net/1/V4/IP"'.format(
                    ident=self.ident
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


class VirtualboxMachinesSettings(BaseSettings):
    @property
    def distribution(self):
        return self.data.get('distribution')

    @property
    def release(self):
        return self.data.get('release')

    @property
    def number(self):
        return int(self.data.get('number', 1))

    @property
    def username(self):
        return self.data.get('username')

    @property
    def password(self):
        return self.data.get('password')


class VirtualboxMachinesProvider(MachinesProvider):
    provider_name = 'virtualbox'
    settings_class = VirtualboxMachinesSettings
    machine_class = VirtualboxMachine
