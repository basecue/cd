from logging import getLogger

from .deployment import Deployment
from .logging import command_logger, control_logging, perform_logging
from .info import VERSION

logger = getLogger(__name__)


class BaseExecutor(object):
    logging = None

    def __init__(self, configuration, environment_name, infrastructure_name, installation):
        self.__class__.logging(configuration.debug.loglevel)

        self.configuration = configuration
        self.environment_name = environment_name
        self.infrastructure_name = infrastructure_name
        self.installation = installation
        self.deployment = Deployment(configuration, environment_name, infrastructure_name, installation)


class Perform(BaseExecutor):
    logging = perform_logging

    def __init__(self, configuration, environment_name, infrastructure_name, installation):
        assert configuration.version == VERSION
        super(Perform, self).__init__(configuration, environment_name, infrastructure_name, installation)
        if configuration.debug.perform_command_output:
            command_logger.set_perform_command_output()

    def install(self):
        self.deployment.provision()


class Control(BaseExecutor):
    logging = control_logging

    def install(self):
        logger.info("Installation project '{project}' environment '{environment}' infrastructure '{infrastructure}' installation '{installation}'".format(
            project=self.configuration.project,
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            installation=self.installation
        ))

        # create isolation
        isolation = self.deployment.isolation()

        logger.info('Transfer of control.')
        # predani rizeni

        command_logger.set_control_perform_command_output()
        isolation.execute('codev install -d {environment} {infrastructure} {installation} --perform -f'.format(
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            installation=self.installation,
        ))
        logger.info('Installation successful.')

    def join(self):
        logger.info('Transfer of control.')
        command_logger.set_control_perform_command_output()
        self.deployment.performer.join()
        logger.info('Join successful.')

    def execute(self, command):
        isolation = self.deployment.isolation()
        logger.info('Transfer of control.')
        command_logger.set_control_perform_command_output()
        isolation.execute(command)
