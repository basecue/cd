from .configuration import YAMLConfiguration
from os import unlink
from .deployment import Deployment


class BaseExecutor(object):
    def __init__(self, configuration, environment_name, infrastructure_name, version):
        self.configuration = configuration
        self.environment_name = environment_name
        self.infrastructure_name = infrastructure_name
        self.version = version
        self.deployment = Deployment(configuration, environment_name, infrastructure_name, version)

    def run(self):
        pass


class Perform(BaseExecutor):
    def install(self):
        # infrastructure provision
        infrastructure = self.deployment.infrastructure

        # configuration provision
        print(infrastructure.machines)


        # provision = self.deployment.provision()


class Control(BaseExecutor):
    def install(self):
        # create isolation
        isolation = self.deployment.isolation

        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        isolation.execute('pip3 install codev=={version}'.format(version=self.configuration.version))

        # send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        isolation.send_file('tmp', '.codev')
        unlink('tmp')

        # predani rizeni
        output = isolation.execute('codev install {environment} {infrastructure} {version} -m perform -f'.format(
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            version=self.version
        ))
        print(output)
