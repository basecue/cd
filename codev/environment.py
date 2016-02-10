from .isolation import IsolationProvider
from .infrastructure import Infrastructure
from .performers import Performer, LocalPerformer

from logging import getLogger
logger = getLogger(__name__)


class Environment(object):
    def __init__(self, configuration):
        self.configuration = configuration

    def performer(self, isolation_ident=None):
        logger.debug(
            "Create performer {performer} isolation ident {isolation_ident}".format(
                performer=self.configuration.performer, isolation_ident=isolation_ident
            )
         )
        return Performer(self.configuration.performer, isolation_ident=isolation_ident)

    def _isolation_provider(self, performer):
        return IsolationProvider(self.configuration.isolation_provider, performer)

    def create_isolation(self, ident, performer=None):
        logger.info("Create isolation '{ident}' at '{performer}'".format(
            ident=ident,
            performer=self.configuration.performer
        ))
        if not performer:
            performer = self.performer(ident)
        return self._isolation_provider(performer).create_isolation(ident)

    def get_isolation(self, ident, performer=None):
        if not performer:
            performer = self.performer(ident)
        return self._isolation_provider(performer).get_isolation(ident)

    def infrastructure(self, infrastructure_name):
        logger.info("Create infrastructure '{infrastructure}'".format(
            infrastructure=infrastructure_name
        ))
        return Infrastructure(self.configuration.infrastructures[infrastructure_name], LocalPerformer())



