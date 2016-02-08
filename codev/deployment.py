from .isolation import IsolationProvider
from .performers import Performer
from .infrastructure import Infrastructure

from logging import getLogger
logger = getLogger('')


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        environment_configuration = configuration.environments[environment_name]
        self.infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        logger.info("Setting up performer: '{performer}'.".format(performer=environment_configuration.performer))
        performer = Performer(environment_configuration.performer)

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

        logger.info(
            "Setting up isolation: '{isolation_provider}'.".format(
                isolation_provider=environment_configuration.isolation_provider
            )
        )
        self.isolation_provider = IsolationProvider(environment_configuration.isolation_provider, performer, isolation_ident)

        self._isolation = None
        self._infrastructure = None

    def isolation(self):
        if not self._isolation:
            logger.info("Creating isolation...")
            self._isolation = self.isolation_provider.isolation()
        return self._isolation

    def infrastructure(self):
        if not self._infrastructure:
            logger.info("Creating infrastructure...")
            self._infrastructure = Infrastructure(self.isolation(), self.infrastructure_configuration)
        return self._infrastructure

