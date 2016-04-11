from .provider import BaseProvider
from .performer import BaseRunner, BasePerformer


class BaseIsolator(BaseRunner, BasePerformer):
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

    def run_script(self, script, arguments=None, logger=None):
        codev_script = 'codev run {script} --performer=local --isolator=none'.format(script=script)
        super(BaseIsolator, self).run_script(codev_script, arguments=arguments, logger=logger)

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
