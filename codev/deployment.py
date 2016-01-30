class Deployment(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version_name):
        try:
            self.environment = configuration.environments[environment_name]
        except KeyError:
            raise ValueError(environment_name)

        try:
            self.infrastructure = self.environment.infrastructures[infrastructure_name]
        except KeyError:
            raise ValueError(infrastructure_name)

        if version_name not in self.environment.versions:
            raise ValueError(version_name)

        self.version = version_name
        self.configuration = configuration

    def isolate(self):
        isolation_name = '%s_%s_%s_%s' % (
            self.configuration.project,
            self.environment.name,
            self.infrastructure.name,
            self.version
        )

        return self.environment.isolation_class(self.environment.performer, isolation_name)
