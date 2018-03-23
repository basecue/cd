from typing import TypeVar, Dict

from codev.core.utils import Status
from codev.core.settings import BaseSettings, ConfigurationScriptsSettings, HasSettings


class ConfigurationSettings(BaseSettings):

    @property
    def scripts(self):
        return ConfigurationScriptsSettings(self.data.get('scripts', {}))

    def parse_option(self, option: str) -> None:
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
    def load_vars(self) -> Dict[str, str]:
        return self.data.get('load_vars', {})


ConfigurationType = TypeVar('ConfigurationType', bound='ConfigurationType')


class Configuration(HasSettings):
    settings_class = ConfigurationSettings

    def __init__(self, name: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = name

    @classmethod
    def get(cls, name: str, configurations: Dict, option: str) -> ConfigurationType:
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
    def loaded_vars(self) -> Dict[str, str]:
        return {
            var: open(file).read() for var, file in self.settings.load_vars.items()
        }

    @property
    def status(self) -> Status:
        return Status(
            name=self.name,
            option=self.option
        )
