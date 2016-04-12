from .provider import BaseProvider
from .performer import BaseProxyPerformer


class BaseIsolator(BaseProxyPerformer):
    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def make_link(self, source, target):
        raise NotImplementedError()

    @property
    def ip(self):
        raise NotImplementedError()

    def redirect(self, machine, source_port, target_port):
        redirection = dict(
            source_port=source_port,
            target_port=target_port,
            source_ip=machine.ip,
            target_ip=self.ip
        )

        self.execute('iptables -t nat -A PREROUTING --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))
        self.execute('iptables -t nat -A POSTROUTING -p tcp --dst {source_ip} --dport {source_port} -j SNAT --to-source {target_ip}'.format(**redirection))
        self.execute('iptables -t nat -A OUTPUT --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(**redirection))


class Isolator(BaseProvider):
    provider_class = BaseIsolator
