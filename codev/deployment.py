from .isolations import Isolation
from .performers import Performer
from .infrastructures import Infrastructure


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        #check
        environment_configuration = configuration.environments[environment_name]
        self.infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        self.performer = Performer(environment_configuration.performer)
        self.isolation_provider = environment_configuration.isolation_provider
        self.isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

        self._isolation = None
        self._infrastructure = None

    @property
    def isolation(self):
        if not self._isolation:
            self._isolation = Isolation(self.performer, self.isolation_provider, self.isolation_ident)
        return self._isolation

    @property
    def infrastructure(self):
        if not self._infrastructure:
            self._infrastructure = Infrastructure(self.isolation, self.infrastructure_configuration)
        return self._infrastructure

