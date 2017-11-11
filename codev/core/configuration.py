from codev.control import Isolation
from codev.core.executor import Executor
from codev.core.settings import BaseSettings, ListDictSettings, ProviderSettings, DictSettings, InfrastructureSettings, \
    IsolationSettings, TaskSettings, ConfigurationScriptsSettings, HasSettings
from codev.core.source import Source


class ConfigurationSettings(BaseSettings):
    # def __init__(self, data, default_sources):
    #     super().__init__(data)
    #     self.default_sources = default_sources


    @property
    def infrastructure(self):
        return DictSettings(InfrastructureSettings, self.data.get('infrastructure', {}))

    @property
    def tasks(self):
        return DictSettings(
            TaskSettings,
            self.data.get('tasks', {})
        )

    @property
    def scripts(self):
        return ConfigurationScriptsSettings(self.data.get('scripts', {}))


    def parse_option(self, option):
        if option:
            try:
                self.data.update(
                    self.data['options'][option]
                )
            except KeyError:
                raise ValueError(
                    "Option '{option}' is not found in configuration.".format(
                        option=option,
                    ),
                    option
                )


class Configuration(HasSettings):
    settings_class = ConfigurationSettings


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
        try:
            return Source(name, settings_data=self.settings.sources[name], option=option)
        except KeyError:
            raise ValueError()

    def get_isolation(self, ident):
        return Isolation(
            self.settings.isolation.provider,
            settings_data=self.settings.isolation.settings_data,
            ident=ident,
            executor=self.executor,
        )