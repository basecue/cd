from .isolation import IsolationProvider
from .infrastructure import Infrastructure

from logging import getLogger
logger = getLogger(__name__)


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        environment_configuration = configuration.environments[environment_name]
        self.infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        self.performer_name = environment_configuration.performer

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

        logger.info(
            "Configure isolation: '{isolation_provider}'.".format(
                isolation_provider=environment_configuration.isolation_provider
            )
        )
        self.isolation_provider = IsolationProvider(environment_configuration.isolation_provider, isolation_ident)

        self._isolation = None
        self._infrastructure = None

    def isolation(self, performer):
        if not self._isolation:
            logger.info("Creating isolation...")
            self._isolation = self.isolation_provider.isolation(performer)
            logger.info('Isolation created.')
        return self._isolation

    def infrastructure(self, performer):
        if not self._infrastructure:
            logger.info("Creating infrastructure...")
            self._infrastructure = Infrastructure(performer, self.infrastructure_configuration)
            logger.info("Infrastructure created.")
        return self._infrastructure

