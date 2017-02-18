from hashlib import md5
from time import time

from .provider import Provider, ConfigurableProvider
from .performer import ProxyPerformer


class Isolator(Provider, ConfigurableProvider, ProxyPerformer):
    def __init__(self, *args, ident=None, **kwargs):
        ident = str(ident or time())
        self.ident = md5(ident.encode()).hexdigest()
        super().__init__(*args, **kwargs)

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
        self.execute(
            'iptables -t nat -A PREROUTING -p tcp --dport {source_port} -j DNAT --to-destination {ip}:{target_port}'.format(
                source_port=source_port,
                target_port=target_port,
                ip=source_ip
            )
        )
        self.execute('iptables -t nat -A POSTROUTING -j MASQUERADE')
