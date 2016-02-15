from codev.provision import Provision, BaseProvision
from codev.provider import ConfigurableProvider
from codev.configuration import BaseConfiguration

from logging import getLogger
logger = getLogger(__name__)


class AnsibleProvisionConfiguration(BaseConfiguration):
    @property
    def playbook(self):
        return self.data.get('playbook', None)

    @property
    def version(self):
        return self.data.get('version', None)


class AnsibleProvision(BaseProvision, ConfigurableProvider):
    configuration_class = AnsibleProvisionConfiguration

    def install(self):
        self.performer.execute('apt-get install python-dev python-pip -y --force-yes')
        version_add = ''
        if self.configuration.version:
            version_add = '==%s' % self.configuration.version
        self.performer.execute('pip install --upgrade ansible%s' % version_add)

    def run(self, machines):
        logger.debug('machines: %s' % machines)
        playbook = self.configuration.playbook.format(infrastructure=self.infrastructure_name)
        inventory = '' #TODO
        self.performer.execute('ansible-playbook -i {inventory} {playbook}'.format(
            inventory=inventory,
            playbook=playbook
        ))


Provision.register('ansible', AnsibleProvision)
