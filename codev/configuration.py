from .info import VERSION
from os import path
import yaml

from collections import OrderedDict

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


class BaseConfiguration(object):
    def __init__(self, data):
        self.data = data


class MachinesConfiguration(BaseConfiguration):
    @property
    def provider(self):
        return self.data.get('provider')

    @property
    def specific(self):
        return self.data.get('specific', {})


class DictConfiguration(OrderedDict):
    def __init__(self, cls, data):
        super(DictConfiguration, self).__init__()
        for name, itemdata in data.items():
            self[name] = cls(itemdata)


class InfrastructureConfiguration(BaseConfiguration):
    @property
    def machines(self):
        return DictConfiguration(MachinesConfiguration, self.data.get('machines', {}))


class EnvironmentConfiguration(BaseConfiguration):
    @property
    def performer(self):
        return self.data.get('performer')

    @property
    def isolation_provider(self):
        return self.data.get('isolation')

    @property
    def infrastructures(self):
        return DictConfiguration(InfrastructureConfiguration, self.data.get('infrastructures', {}))

    @property
    def versions(self):
        return self.data.get('versions', [])


class Configuration(BaseConfiguration):

    def __init__(self, data=None):
        super(Configuration, self).__init__(self.default_data)
        if data:
            self.data.update(data)
        self.current_data = None

    @property
    def default_data(self):
        return OrderedDict((
            ('version', VERSION),
            ('project', path.basename(path.abspath(path.curdir))),
            ('environments', {})
        ))

    @property
    def version(self):
        return self.data['version']

    @property
    def project(self):
        return self.data['project']

    @property
    def environments(self):
        return DictConfiguration(EnvironmentConfiguration, self.data['environments'])


class YAMLConfiguration(Configuration):
    @classmethod
    def from_configuration(cls, configuration):
        return cls(configuration.data)

    @classmethod
    def from_file(cls, filepath):
        return cls.from_yaml(open(filepath))

    @classmethod
    def from_yaml(cls, yamldata):
        return cls(yaml.load(yamldata))

    def save_to_file(self, filepath):
        yaml.dump(self.data, open(filepath, 'w+'))

