from os import unlink

from logging import getLogger
from logging.config import dictConfig

from .configuration import YAMLConfiguration
from .environment import Environment
from .logging import command_logger, control_config, perform_config

logger = getLogger(__name__)


class BaseExecutor(object):
    logging_config = None

    def __init__(self, configuration, environment_name):
        dictConfig(self.logging_config)

        self.environment = Environment(configuration.environments[environment_name])


class Perform(BaseExecutor):
    logging_config = perform_config

    def install(self, infrastructure_name, version):
        # infrastructure provision
        infrastructure = self.environment.infrastructure(infrastructure_name)

        # configuration provision
        print(infrastructure.machines)


        # provision = self.deployment.provision()


class Control(BaseExecutor):
    logging_config = control_config

    def __init__(self, configuration, environment_name):
        super(Control, self).__init__(configuration, environment_name)
        self.configuration = configuration
        self.environment_name = environment_name

    def install(self, infrastructure_name, installation):
        logger.info("Installation project '{project}' environment '{environment}' infrastructure '{infrastructure}' installation '{installation}'".format(
            project=self.configuration.project,
            environment=self.environment_name,
            infrastructure=infrastructure_name,
            installation=installation
        ))

        # create isolation
        isolation_ident = '%s_%s_%s_%s' % (
            self.configuration.project,
            self.environment_name,
            infrastructure_name,
            installation
        )

        isolation = self.environment.isolation(isolation_ident)

        logger.info("Installation codev version '{version}'".format(
            version=self.configuration.version
        ))
        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')
        # install proper version of codev
        isolation.execute('pip3 install --upgrade codev=={version}'.format(version=self.configuration.version))


        # send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        isolation.send_file('tmp', '.codev')
        unlink('tmp')

        logger.info('Transfer of control.')
        # predani rizeni

        command_logger.set_control_perform_mode()
        isolation.execute('codev install {environment} {infrastructure} {installation} -m perform -f'.format(
            environment=self.environment_name,
            infrastructure=infrastructure_name,
            installation=installation
        ))
        logger.info('Installation successful.')

