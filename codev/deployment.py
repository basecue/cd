from .isolations import IsolationProvider
from .performers import Performer
from .infrastructures import Infrastructure


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        environment_configuration = configuration.environments[environment_name]
        self.infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        performer = Performer(environment_configuration.performer)

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

        self.isolation_provider = IsolationProvider(environment_configuration.isolation_provider, performer, isolation_ident)

        self._isolation = None
        self._infrastructure = None

    def isolation(self):
        if not self._isolation:
            self._isolation = self.isolation_provider.isolation()
        return self._isolation

    def infrastructure(self):
        if not self._infrastructure:
            self._infrastructure = Infrastructure(self.isolation(), self.infrastructure_configuration)
        return self._infrastructure

