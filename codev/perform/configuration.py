from codev.core.configuration import ConfigurationSettings, Configuration
from codev.core.settings import DictSettings, TaskSettings
from codev.perform.infrastructure import Infrastructure


class ConfigurationPerformSettings(ConfigurationSettings):

    @property
    def tasks(self):
        return DictSettings(
            TaskSettings,
            self.data.get('tasks', {})
        )

    @property
    def infrastructure(self):
        return self.data.get('infrastructure', {})


class ConfigurationPerform(Configuration):
    settings_class = ConfigurationPerformSettings

    def get_infrastructure(self, executor):
        return Infrastructure(
            settings_data=self.settings.infrastructure,
            executor=executor,
        )

    # @property
    # def status(self):
    #     return super().status