from .environment import Environment
from .infrastructure import Infrastructure


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, installation_name):
        #check
        environment_configuration = configuration.environments[environment_name]
        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if installation_name not in environment_configuration.installations:
            raise ValueError('Bad installation')

        self.environment = Environment(environment_configuration)
        self.infrastructure = Infrastructure(infrastructure_configuration)

        self.isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            installation_name
        )