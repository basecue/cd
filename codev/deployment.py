from .isolations import Isolation
from .performers import Performer
from .infrastructures import Infrastructure


class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        #check
        environment_configuration = configuration.environments[environment_name]
        infrastructure_configuration = environment_configuration.infrastructures[infrastructure_name]
        if version_name not in environment_configuration.versions:
            raise ValueError('Bad version')

        performer = Performer(environment_configuration.performer)

        isolation_ident = '%s_%s_%s_%s' % (
            configuration.project,
            environment_name,
            infrastructure_name,
            version_name
        )

        self.isolation = Isolation(performer, environment_configuration.isolation_provider, isolation_ident)
        self.infrastructure = Infrastructure(self.isolation, infrastructure_configuration)

