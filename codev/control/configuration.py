from typing import Dict, Any

from codev.control.isolation import IsolationProvider, Isolation
from codev.core.configuration import ConfigurationSettings, Configuration


class ConfigurationControlSettings(ConfigurationSettings):

    @property
    def isolation(self) -> Dict[str, Any]:
        return self.data.get('isolation', {})


class ConfigurationControl(Configuration):
    settings_class = ConfigurationControlSettings

    def get_isolation(
        self,
        project_name: str,
        source_name: str,
        source_option: str,
        next_source_name: str,
        next_source_option: str
    ) -> Isolation:
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
