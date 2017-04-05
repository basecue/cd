from hashlib import sha256
from time import time

from slugify import slugify

from .provider import Provider, ConfigurableProvider
from .performer import ProxyPerformer


class Isolator(Provider, ConfigurableProvider, ProxyPerformer):
    def __init__(self, *args, ident=None, **kwargs):
        ident = ':'.join(ident) if ident else str(time())
        ident_hash = sha256(ident.encode()).hexdigest()
        self.ident = '{}:{}'.format(
            ident_hash[:10],
            slugify(ident, regex_pattern=r'[^-a-z0-9_:]+')
        )
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
    def status(self):
        return {}

    @property
    def ip(self):
        return '127.0.0.1'

    def redirect(self, machine_ip, isolator_port, machine_port):
        self.execute(
            'iptables -t nat -A PREROUTING -p tcp --dport {isolator_port} -j DNAT -d {isolator_ip} --to-destination {machine_ip}:{machine_port}'.format(
                isolator_port=isolator_port,
                machine_port=machine_port,
                isolator_ip=self.ip,
                machine_ip=machine_ip
            )
        )
        self.execute('iptables -t nat -A POSTROUTING -j MASQUERADE')
