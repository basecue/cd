from typing import TypeVar, Dict

from codev.core.utils import Status
from codev.core.settings import BaseSettings, ConfigurationScriptsSettings, HasSettings


class ConfigurationSettings(BaseSettings):

    @property
    def scripts(self):
        return ConfigurationScriptsSettings(self.data.get('scripts', {}))

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
    def get(cls, name: str, configurations: Dict) -> ConfigurationType:
        try:
            settings_data = configurations[name]
        except KeyError:
            raise ValueError(
                "Configuration '{name}' is not found.".format(
                    name=name
                )
            )
        return cls(name, settings_data=settings_data)

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
