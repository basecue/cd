in-target echo "{username} ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
in-target mkdir /root/.ssh
in-target cat > /root/.ssh/authorized_keys << EOF_id_rsa_pub
{ssh_authorized_keys}
EOF_id_rsa_pub
in-target chown root:root -R /root/.ssh
in-target chmod 700 -R /root/.ssh

# Modify sshd_config
in-target /bin/sed -i 's/PermitRootLogin no/PermitRootLogin yes/' /etc/ssh/sshd_config
in-target /bin/sed -i 's/PermitRootLogin without-password/PermitRootLogin yes/' /etc/ssh/sshd_config

in-target cp -R /root/.ssh `getent passwd "{username}" | cut -d: -f6`/
in-target chown {username}:{username} -R `getent passwd "{username}" | cut -d: -f6`/.ssh

in-target echo "vboxsf" >> /etc/modules
{fstab}