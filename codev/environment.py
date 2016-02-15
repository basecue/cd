from .isolation import IsolationProvider
from .performer import Performer
from .infrastructure import Infrastructure

from logging import getLogger
logger = getLogger(__name__)


class Environment(object):
    def __init__(self, configuration, infrastructure_name, isolation_ident):
        self.performer = Performer(
            configuration.performer.provider,
            configuration_data=configuration.performer.specific,
            isolation_ident=isolation_ident
        )

        self._isolation_provider = IsolationProvider(
            configuration.isolation_provider,
            self.performer,
            isolation_ident
        )

        infrastructure_configuration = configuration.infrastructures[infrastructure_name]
        self._infrastructure = Infrastructure(infrastructure_name, infrastructure_configuration)

    def create_isolation(self):
        return self._isolation_provider.create_isolation()

    def provision(self):
        self._infrastructure.provision()




