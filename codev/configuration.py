from .performers import Performer
from .isolations import Isolation
from .infrastructures import InfrastructureProvision

from .info import VERSION
from os import path
import yaml

from collections import OrderedDict


_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)


class BaseConfiguration(object):
    def __init__(self, config):
        self._config = config


class NamedConfiguration(BaseConfiguration):
    def __init__(self, name, config):
        self.name = name
        super(NamedConfiguration, self).__init__(config)


class CurrentConfiguration(object):
    @property
    def mode(self):
        return 'control' + 'perform'

    @property
    def infrastructure(self):
        return ''

    @property
    def environment(self):
        return ''

    @property
    def version(self):
        return ''


class Machines(NamedConfiguration):
    pass


class DictConfiguration(OrderedDict):
    def __init__(self, cls, config):
        super(DictConfiguration, self).__init__()
        for name, configuration in config.items():
            self[name] = cls(name, configuration)


class Infrastructure(NamedConfiguration):
    def machines(self):
        return DictConfiguration(Machines, self._config.get('machines', {}))

    def provision(self):
        return InfrastructureProvision(self._config.get('provision', 'real'))


class Environment(NamedConfiguration):
    @property
    def performer(self):
        return Performer(self._config.get('performer', 'local'))

    @property
    def isolation(self):
        return Isolation(self._config.get('isolation', 'lxc'))

    @property
    def infrastructures(self):
        return DictConfiguration(Infrastructure, self._config.get('infrastructures', {}))

    @property
    def versions(self):
        return ''


class Configuration(BaseConfiguration):
    @property
    def version(self):
        return self._config.get('version', VERSION)

    @property
    def project(self):
        return self._config.get('project', path.basename(path.abspath(path.curdir)))

    @property
    def environments(self):
        return DictConfiguration(Environment, self._config.get('environments', {}))

    def current(self):
        return CurrentConfiguration()


class YAMLConfiguration(Configuration):
    @classmethod
    def from_file(cls, filepath):
        return cls(open(filepath))

    def __init__(self, yamlconfig):
        super(YAMLConfiguration, self).__init__(yaml.load(yamlconfig))

    def save_to_file(self, filepath):
        yaml.dump(self._config, open(filepath, 'w'))
