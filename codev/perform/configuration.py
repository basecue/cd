from typing import Dict, Any

from codev.core.configuration import ConfigurationSettings, Configuration
from codev.core.executor import BareExecutor
from codev.core.settings import DictSettings
from codev.perform.infrastructure import Infrastructure
from codev.perform.task import TaskSettings


class ConfigurationPerformSettings(ConfigurationSettings):

    @property
    def tasks(self) -> DictSettings:
        return DictSettings(
            TaskSettings,
            self.data.get('tasks', {})
        )

    @property
    def infrastructure(self) -> Dict[str, Any]:
        return self.data.get('infrastructure', {})


class ConfigurationPerform(Configuration):
    settings_class = ConfigurationPerformSettings

    def get_infrastructure(self, executor: BareExecutor) -> Infrastructure:
        return Infrastructure(
            settings_data=self.settings.infrastructure,
            executor=executor,
        )

    # @property
    # def status(self):
    #     return super().status