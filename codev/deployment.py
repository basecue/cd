from .environment import Environment
from .infrastructure import Infrastructure
from .performers import LocalPerformer


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name):
        #check
        environment_configuration = configuration.environments[environment_name]
        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if installation_name not in environment_configuration.installations:
            raise ValueError('Bad installation')

        self._environment = Environment(environment_configuration)
        self._infrastructure = Infrastructure(infrastructure_configuration)

        self.isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name
        )

    def performer(self):
        return self._environment.performer(self.isolation_ident)

    def create_isolation(self):
        return self._environment.create_isolation(self.isolation_ident)

    def create_infrastructure(self):
        return self._infrastructure.create_machines(LocalPerformer())

    def provision(self, machines):
        pass
