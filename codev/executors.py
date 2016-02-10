from os import unlink

from logging import getLogger

from .configuration import YAMLConfiguration
from .environment import Environment
from .logging import command_logger, control_logging, perform_logging

logger = getLogger(__name__)


class BaseExecutor(object):
    logging = None

    def __init__(self, configuration, environment_name, infrastructure_name, installation):
        self.__class__.logging(configuration.debug.loglevel)
        try:
            self.environment = Environment(configuration.environments[environment_name])
        except KeyError:
            raise ValueError(
                "Environment '{environment_name}' does not exist.".format(environment_name=environment_name)
            )
        self.configuration = configuration
        self.environment_name = environment_name
        self.infrastructure_name = infrastructure_name
        self.installation = installation

    @property
    def deployment(self):
        return dict(
            project=self.configuration.project,
            environment=self.environment_name,
            infrastructure=self.infrastructure_name,
            installation=self.installation
        )


class Perform(BaseExecutor):
    logging = perform_logging

    def __init__(self, configuration, environment_name, infrastructure_name, installation):
        super(Perform, self).__init__(configuration, environment_name, infrastructure_name, installation)
        if configuration.debug.perform_command_output:
            command_logger.set_perform_command_output()

    def install(self):
        # infrastructure provision
        infrastructure = self.environment.infrastructure(self.infrastructure_name)

        # configuration provision
        from time import sleep
        for i in range(1, 200):
            logger.info(i)
            sleep(0.25)


        # provision = self.deployment.provision()


class Control(BaseExecutor):
    logging = control_logging

    def __init__(self, configuration, environment_name, infrastructure_name, installation):
        super(Control, self).__init__(configuration, environment_name, infrastructure_name, installation)

    @property
    def isolation_ident(self):
        return '{project}_{environment}_{infrastructure}_{installation}'.format(**self.deployment)

    def install(self):
        logger.info("Installation project '{project}' environment '{environment}' infrastructure '{infrastructure}' installation '{installation}'".format(
            **self.deployment
        ))

        # create isolation
        isolation = self.environment.create_isolation(self.isolation_ident)

        logger.info("Installation codev version '{version}'".format(
            version=self.configuration.version
        ))
        # install python3 pip
        isolation.execute('apt-get install python3-pip -y --force-yes')

        # install proper version of codev
        if self.configuration.debug.distfile:
            isolation.send_file(self.configuration.debug.distfile.format(version=self.configuration.version), 'codev.tar.gz')
            isolation.execute('pip3 install --upgrade codev.tar.gz')
        else:
            isolation.execute('pip3 install --upgrade codev=={version}'.format(version=self.configuration.version))

        # send configuration file
        YAMLConfiguration.from_configuration(self.configuration).save_to_file('tmp')
        isolation.send_file('tmp', '.codev')
        unlink('tmp')

        logger.info('Transfer of control.')
        # predani rizeni

        command_logger.set_control_perform_command_output()
        isolation.execute('codev install {environment} {infrastructure} {installation} -m perform -f'.format(
            **self.deployment
        ))
        logger.info('Installation successful.')

    def control(self):
        isolation = self.environment.get_isolation(self.isolation_ident, performer=self.environment.performer())
        if not isolation:
            raise ValueError("Isolation of project '{project}' environment '{environment}' infrastructure '{infrastructure}' installation '{installation}' does not exists.".format(
                **self.deployment
            ))

        logger.info('Transfer of control.')
        command_logger.set_control_perform_command_output()
        self.environment.performer(self.isolation_ident).join()
