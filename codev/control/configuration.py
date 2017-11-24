from codev.control.isolation import  IsolationProvider
from codev.core.configuration import ConfigurationSettings, Configuration


class ConfigurationControlSettings(ConfigurationSettings):

    @property
    def isolation(self):
        return self.data.get('isolation', {})


class ConfigurationControl(Configuration):
    settings_class = ConfigurationControlSettings

    def get_isolation(self, project_name, source_name, source_option, next_source_name, next_source_option):

        return IsolationProvider(
            settings_data=self.settings.isolation,
            project_name=project_name,
            configuration_name=self.name,
            configuration_option=self.option,
            source_name=source_name,
            source_option=source_option,
            next_source_name=next_source_name,
            next_source_option=next_source_option
        ).isolation()
