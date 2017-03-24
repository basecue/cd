from .providers import *


class CodevCore(object):

    def __init__(
        self,
        settings,
        configuration_name,
        configuration_option=''
    ):
        self.project_name = settings.project

        try:
            self.configuration_settings = settings.configurations[configuration_name]
        except KeyError:
            raise ValueError(
                "Configuration '{configuration_name}' is not found.".format(
                    configuration_name=configuration_name,
                    project_name=self.project_name
                )
            )

        if configuration_option:
            try:
                self.configuration_settings = self.configuration_settings.options[configuration_option]
            except KeyError:
                raise ValueError(
                    "Option '{configuration_option}' is not found in configuration '{configuration_name}'.".format(
                        configuration_name=configuration_name,
                        configuration_option=configuration_option,
                        project_name=self.project_name
                    )
                )

        self.configuration_name = configuration_name
        self.configuration_option = configuration_option