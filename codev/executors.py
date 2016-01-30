from .configuration import YAMLConfiguration
from os import unlink


class BaseExecutor(object):
    def __init__(self, configuration, deployment):
        self.configuration = configuration
        self.deployment = deployment

    def run(self):
        pass


class Perform(BaseExecutor):
    def install(self):
        # infrastructure provision
        # infrastructure = self.infrastructure_class(self.configuration)
        pass


class Control(BaseExecutor):
    def install(self):
        # create isolation
        isolation = self.deployment.isolate()

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y')

        # install proper version of codev
        isolation.execute('pip3 install codev=={version}'.format(version=self.configuration.version))

        # send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        isolation.send_file('tmp', '.codev')
        unlink('tmp')

        # predani rizeni
        output = isolation.execute('codev install {environment} {infrastructure} {version} -m perform -f'.format(
            environment=self.deployment.environment,
            infrastructure=self.deployment.infrastructure,
            version=self.deployment.version
        ))
        print(output)
