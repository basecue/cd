from collections import OrderedDict
from os import path

import yaml

from codev import __version__
from codev.core.configuration import Configuration
from codev.core.settings import HasSettings, BaseSettings
from codev.core.utils import Status

"""
YAML OrderedDict mapping
http://stackoverflow.com/questions/5121931/in-python-how-can-you-load-yaml-mappings-as-ordereddicts
"""
_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.items())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)
"""
"""


class CodevSettings(BaseSettings):
    @property
    def version(self):
        return self.data.get('version', __version__)

    @property
    def project(self):
        return self.data.get('project', path.basename(path.abspath(path.curdir)))

    @property
    def configurations(self):
        return self.data.get('configurations', {})


class Codev(HasSettings):
    settings_class = CodevSettings
    configuration_class = Configuration

    def __init__(self, *args, configuration_name='', configuration_option='', **kwargs):
        super().__init__(*args, **kwargs)

        self.configuration = self.configuration_class.get(
            configuration_name,
            self.settings.configurations,
            configuration_option
        )

    @classmethod
    def from_file(cls, filepath, *args, **kwargs):
        with open(filepath) as file:
            return cls.from_yaml(file, *args, **kwargs)

    @classmethod
    def from_yaml(cls, yamldata, *args, **kwargs):
        settings_data = yaml.load(yamldata)
        return cls(*args, settings_data=settings_data, **kwargs)

    @property
    def version(self):
        return self.settings.version

    # def save_to_file(self, filepath):
    #     with open(filepath, 'w+') as file:
    #         yaml.dump(self.settings.data, file)

    @property
    def status(self):
        """
        Info about runner

        :return: runner status
        :rtype: dict
        """
        return Status(
            project=self.settings.project,
            configuration=self.configuration.status,
        )
