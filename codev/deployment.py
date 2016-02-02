from .isolations import Isolation
from .infrastructures import Infrastructure


class Environment(object):
    def __init__(self, environment_configuration, infrastructure_configuration):
        self.isolation = Isolation(
            environment_configuration.isolation_provider,
            environment_configuration.performer
        )
        self.infrastructure = Infrastructure(
            infrastructure_configuration.provider,
            infrastructure_configuration.machines
        )


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        environment_configuration = configuration.environments[environment_name]
        self.environment = Environment(
            environment_configuration,
            environment_configuration.infrastructures[infrastructure_name]
        )
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        self.isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

    def isolation(self):
        return self.environment.isolation(self.isolation_ident)

    def infrastructure(self):
        self.environment.infrastructure()
