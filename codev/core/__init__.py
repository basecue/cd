from .providers import *


class CodevCore(object):

    def __init__(
        self,
        settings,
        configuration_name,
        configuration_option=''
    ):
        self.project_name = settings.project

        self.configuration_settings = settings.get_current_configuration(configuration_name, configuration_option)
        self.configuration_name = configuration_name
        self.configuration_option = configuration_option
