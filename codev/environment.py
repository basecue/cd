from .isolation import IsolationProvider
from .infrastructure import Infrastructure
from .performers import Performer, LocalPerformer

from logging import getLogger
logger = getLogger(__name__)


class Environment(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def isolation(self, ident):
        logger.info("Create isolation '{ident}' at '{performer}'".format(
            ident=ident,
            performer=self.configuration.performer
        ))
        performer = Performer(self.configuration.performer, ident)
        isolation_provider = IsolationProvider(self.configuration.isolation_provider, performer)
        return isolation_provider.isolation(ident)

    def infrastructure(self, infrastructure_name):
        logger.info("Create infrastructure '{infrastructure}'".format(
            infrastructure=infrastructure_name
        ))
        return Infrastructure(self.configuration.infrastructures[infrastructure_name], LocalPerformer())



