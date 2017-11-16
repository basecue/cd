from codev.control.isolation import Isolation
from codev.core.configuration import ConfigurationSettings, Configuration
from codev.core.executor import Executor
from codev.core.settings import ListDictSettings, ProviderSettings, IsolationSettings
from codev.core.source import Source


class ConfigurationControlSettings(ConfigurationSettings):
    @property
    def sources(self):
        return ListDictSettings(
            self.data.get('sources', [])
        )

    @property
    def executor(self):
        return ProviderSettings(self.data.get('executor', {}))

    @property
    def isolation(self):
        return IsolationSettings(self.data.get('isolation', {}))

    @property
    def loaded_vars(self):
        return {
            var: open(file).read() for var, file in self.data.get('load_vars', {}).items()
        }


class ConfigurationControl(Configuration):
    settings_class = ConfigurationControlSettings

    @property
    def executor(self):
        executor_provider = self.settings.executor.provider
        executor_settings_data = self.settings.executor.settings_data

        return Executor(
            executor_provider,
            settings_data=executor_settings_data
        )

    def get_source(self, name, option):
        return Source.get(name, self.settings.sources, option)

    def get_isolation(self, ident):
        return Isolation(
            self.settings.isolation.provider,
            settings_data=self.settings.isolation.settings_data,
            ident=ident,
            executor=self.executor,
            configuration_name=self.name,
            configuration_option=self.option
        )

    # @property
    # def status(self):
    #     return super().status