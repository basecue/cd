from logging import getLogger

from codev_core.performer import Performer
from codev_core.source import Source

from .configuration import Configuration
from .isolator import Isolator


logger = getLogger(__name__)
command_logger = getLogger('command')


class Installation(object):
    """
    Installation of project.
    """
    def __init__(
            self,
            settings,
            environment_name,
            configuration_name='',
            source_name='',
            source_options='',
            next_source_name='',
            next_source_options=''
    ):

        environment_settings = settings.environments[environment_name]
        self.environment_name = environment_name
        self.project_name = settings.project

        # source
        if source_name:
            try:
                source_settings = environment_settings.sources[source_name]
            except KeyError as e:
                raise ValueError(
                    "Source '{source_name}' is not allowed source for environment '{environment_name}'.".format(
                        source_name=source_name,
                        environment_name=environment_name,
                        project_name=self.project_name
                    )
                ) from e
        else:
            source_name, source_settings = list(environment_settings.sources.items())[0]

        source = Source(
            source_name,
            source_options,
            settings_data=source_settings
        )

        # next source
        if next_source_name:
            next_source = Source(
                next_source_name,
                next_source_options,
                settings_data=source_settings
            )
        else:
            next_source = None

        # performer
        performer_settings = environment_settings.performer
        performer_provider = performer_settings.provider
        performer_settings_data = performer_settings.settings_data

        performer = Performer(
            performer_provider,
            settings_data=performer_settings_data
        )

        isolator_settings = environment_settings.isolator
        isolator_provider = isolator_settings.provider
        isolator_settings_data = isolator_settings.settings_data

        # TODO add codev version?
        ident = sorted(list(dict(
            project=settings.project,
            environment=environment_name,
            configuration=configuration_name,
            source_ident=source.ident,
            next_source_ident=next_source.ident if next_source else ''
        ).items()))

        self.performer = Isolator(isolator_provider, performer=performer, settings_data=isolator_settings_data, ident=ident)

        # configuration
        if configuration_name:
            configuration_settings = environment_settings.configurations[configuration_name]
        else:
            # default configuration is the first configuration in environment
            configuration_name, configuration_settings = list(environment_settings.configurations.items())[0]

        self.configuration_name = configuration_name
        self.configuration = Configuration(
            configuration_settings, source,
            next_source=next_source,
            performer=self.performer
        )

    def deploy(self, input_vars):
        """
        Create machines, install and run provisioner

        :return: True if deployment is successfully realized
        :rtype: bool
        """
        return self.configuration.deploy(self.status, input_vars)

    def destroy(self):
        """
        Destroy the isolation.

        :return: True if isolation is destroyed
        :rtype: bool
        """
        return self.configuration.destroy()

    @property
    def status(self):
        """
        Info about installation

        :return: installation status
        :rtype: dict
        """
        status = dict(
            project=self.project_name,
            environment=self.environment_name,
            configuration=self.configuration_name,
        )
        status.update(self.configuration.status)
        return status
