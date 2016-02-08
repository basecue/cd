from os import unlink

from .configuration import YAMLConfiguration
from .deployment import Deployment
from .performers import performer, LocalPerformer

from logging import getLogger
logger = getLogger(__name__)


class BaseMode(object):
    def __init__(
            self,
            configuration,
            environment_name,
            infrastructure_name,
            version
    ):
        self.configuration = configuration
        self.environment_name = environment_name
        self.infrastructure_name = infrastructure_name
        self.version = version
        logger.info(
            "Setting up deployment '{environment_name}, {infrastructure_name}, {version}'".format(
                environment_name=environment_name,
                infrastructure_name=infrastructure_name,
                version=version
            )
        )

        self.deployment = Deployment(configuration, environment_name, infrastructure_name, version)
        self.performer = None

    def run(self):
        pass


class Perform(BaseMode):
    def __init__(self, *args, **kwargs):
        super(Perform, self).__init__(*args, **kwargs)
        self.performer = LocalPerformer()

    def install(self):
        # infrastructure provision
        infrastructure = self.deployment.infrastructure(self.performer)

        # configuration provision
        print(infrastructure.machines)


        # provision = self.deployment.provision()


class Control(BaseMode):
    def __init__(self, *args, **kwargs):
        super(Control, self).__init__(*args, **kwargs)
        logger.info("Configure performer: '{performer}'.".format(performer=self.deployment.performer_name))
        self.performer = performer(self.deployment.performer_name)
        
    def install(self):
        # create isolation
        isolation = self.deployment.isolation(self.performer)

        logger.info(
            "Instalation codev in isolation at version '{version}'...".format(version=self.configuration.version)
        )
        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')
        # install proper version of codev
        isolation.execute('pip3 install codev=={version}'.format(version=self.configuration.version))


        # send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        isolation.send_file('tmp', '.codev')
        unlink('tmp')

        logger.info('Transfer of control.')
        # predani rizeni
        isolation.execute('codev install {environment} {infrastructure} {version} -m perform -f'.format(
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            version=self.version
        ))
        logger.info('Installation successful.')

