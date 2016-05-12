from hashlib import md5
from time import time

from .provider import Provider, ConfigurableProvider
from .performer import BaseProxyPerformer


class Isolator(Provider, BaseProxyPerformer, ConfigurableProvider):
    def __init__(self, *args, ident=None, **kwargs):
        ident = str(ident or time())
        ident = md5(ident.encode()).hexdigest()
        super().__init__(*args, ident=ident, **kwargs)

    def exists(self):
        raise NotImplementedError()

    def create(self):
        raise NotImplementedError()

    def is_started(self):
        raise NotImplementedError()

    def start(self):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

    def destroy(self):
        raise NotImplementedError()

    def make_link(self, source, target):
        raise NotImplementedError()

    @property
    def info(self):
        return {}

    @property
    def ip(self):
        return '127.0.0.1'

    def redirect(self, source_ip, source_port, target_port):
        redirection = dict(
            source_port=source_port,
            target_port=target_port,
            source_ip=source_ip,
            target_ip=self.ip
        )

        self.execute(
            'iptables -t nat -A PREROUTING --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(
                **redirection
            )
        )
        self.execute(
            'iptables -t nat -A POSTROUTING -p tcp --dst {source_ip} --dport {source_port} -j SNAT --to-source {target_ip}'.format(
                **redirection
            )
        )
        self.execute(
            'iptables -t nat -A OUTPUT --dst {target_ip} -p tcp --dport {target_port} -j DNAT --to-destination {source_ip}:{source_port}'.format(
                **redirection
            )
        )
