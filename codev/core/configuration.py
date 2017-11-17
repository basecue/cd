from codev.core.settings import BaseSettings, ConfigurationScriptsSettings, HasSettings
from codev.core.utils import status


class ConfigurationSettings(BaseSettings):
    # def __init__(self, data, default_sources):
    #     super().__init__(data)
    #     self.default_sources = default_sources

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

    @property
    def load_vars(self):
        return self.data.get('load_vars', {})


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
    def loaded_vars(self):
        return {
            var: open(file).read() for var, file in self.settings.load_vars.items()
        }

    @property
    @status
    def status(self):
        return dict(
            name=self.name,
            option=self.option
        )
