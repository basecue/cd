from codev.core.settings import BaseSettings, DictSettings, InfrastructureSettings, \
    TaskSettings, ConfigurationScriptsSettings, HasSettings
from codev.core.utils import status


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

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    @classmethod
    def get(cls, name, configurations, option):
        try:
            settings_data = configurations[name]
        except KeyError:
            raise ValueError(
                "Configuration '{name}' is not found.".format(
                    name=name
                )
            )
        try:
            return cls(name, settings_data=settings_data, option=option)
        except ValueError as e:
            raise ValueError(
                "Option '{option}' is not found in configuration '{name}'.".format(
                    option=option,
                    name=name
                )
            )

    @property
    @status
    def status(self):
        return dict(
            name=self.name,
            option=self.option
        )
