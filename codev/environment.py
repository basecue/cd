from .isolation import Isolation
from .performer import Performer
from .infrastructure import Infrastructure

from logging import getLogger
logger = getLogger(__name__)


class Environment(object):
    def __init__(self, configuration, infrastructure_name, isolation_ident):
        self.performer = Performer(
            configuration.performer.provider,
            configuration_data=configuration.performer.specific
        )

        self.isolation = Isolation(
            configuration.isolation_provider,
            self.performer,
            isolation_ident
        )

        infrastructure_configuration = configuration.infrastructures[infrastructure_name]
        self._infrastructure = Infrastructure(infrastructure_name, infrastructure_configuration)

    def provision(self):
        return self._infrastructure.provision()




