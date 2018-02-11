echo "{username} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
mkdir /root/.ssh
cat > /root/.ssh/authorized_keys << EOF_id_rsa_pub
{ssh_authorized_keys}
EOF_id_rsa_pub
chown root:root -R /root/.ssh
chmod 700 -R /root/.ssh

# Modify sshd_config
/bin/sed -i 's/PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config
/bin/sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

cp -R /root/.ssh `getent passwd "{username}" | cut -d: -f6`/
chown {username}:{username} -R `getent passwd "{username}" | cut -d: -f6`/.ssh

echo "vboxsf" >> /etc/modules
{fstab}

# ubuntu < 17.10
tee >> /etc/network/interfaces << EOF_interfaces
auto {device_2}
iface {device_2} inet dhcp
EOF_interfaces

# ubuntu >= 17.10
tee > /etc/netplan/{device_2}.yaml << EOF_netplan
network:
 version: 2
 renderer: networkd
 ethernets:
   {device_2}:
     dhcp4: yes
EOF_netplan
