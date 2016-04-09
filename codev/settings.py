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


class BaseSettings(object):
    def __init__(self, data=None):
        if data is None:
            data = {}
        self.data = data

    def __bool__(self):
        return bool(self.data)


class ProviderSettings(BaseSettings):
    @property
    def provider(self):
        return self.data.get('provider')

    @property
    def specific(self):
        return self.data.get('specific', {})


class DictSettings(OrderedDict):
    def __init__(self, cls, data, *args, **kwargs):
        super(DictSettings, self).__init__()
        for name, itemdata in data.items():
            self[name] = cls(itemdata, *args, **kwargs)


class ListDictSettings(OrderedDict):

    @staticmethod
    def _intersect_default_value(intersect_default, key, value):
        ret_val = intersect_default.get(key, {})
        ret_val.update(value)
        return ret_val

    def __init__(self, data, intersect_default=None):
        if intersect_default is None:
            intersect_default = {}
        super(ListDictSettings, self).__init__()

        if isinstance(data, dict) or isinstance(data, OrderedDict):
            for key, value in data.items():
                if not (isinstance(value, dict) or isinstance(value, OrderedDict)):
                    raise ValueError('Object {value} must be dictionary.'.format(value=value))
                self[key] = self.__class__._intersect_default_value(intersect_default, key, value)

        elif isinstance(data, list):
            for obj in data:
                if isinstance(obj, OrderedDict):
                    if len(obj) == 1:
                        key = list(obj.keys())[0]
                        value = obj[key]
                    else:
                        raise ValueError('Object {obj} must have length equal to 1.'.format(obj))
                else:
                    key = obj
                    value = {}
                self[key] = self.__class__._intersect_default_value(intersect_default, key, value)
        else:
            raise ValueError('Object {data} must be list or dictionary.'.format(data=data))


class ProvisionScriptsSettings(BaseSettings):
    @property
    def onstart(self):
        return ListDictSettings(self.data.get('onstart', []))

    @property
    def onsuccess(self):
        return ListDictSettings(self.data.get('onsuccess', []))

    @property
    def onerror(self):
        return ListDictSettings(self.data.get('onerror', []))


class ProvisionSettings(ProviderSettings):
    @property
    def scripts(self):
        return ProvisionScriptsSettings(self.data.get('scripts', {}))


class IsolationScriptsSettings(BaseSettings):
    @property
    def oncreate(self):
        return ListDictSettings(self.data.get('oncreate', []))

    @property
    def onenter(self):
        return ListDictSettings(self.data.get('onenter', []))


class IsolationSettings(BaseSettings):
    @property
    def provider(self):
        return self.data.get('provider')

    @property
    def connectivity(self):
        return ListDictSettings(self.data.get('connectivity', {}))

    @property
    def scripts(self):
        return IsolationScriptsSettings(self.data.get('scripts', {}))


class InfrastructureSettings(BaseSettings):
    @property
    def machines(self):
        return DictSettings(ProviderSettings, self.data.get('machines', {}))

    @property
    def provision(self):
        return ProvisionSettings(self.data.get('provision', {}))

    @property
    def isolation(self):
        return IsolationSettings(self.data.get('isolation', {}))


class EnvironmentSettings(BaseSettings):
    def __init__(self, data, default_installations):
        super(EnvironmentSettings, self).__init__(data)
        self.default_installations = default_installations

    @property
    def performer(self):
        return ProviderSettings(self.data.get('performer', {}))

    @property
    def infrastructures(self):
        return DictSettings(
            InfrastructureSettings,
            self.data.get('infrastructures', {}),
        )

    @property
    def installations(self):
        return ListDictSettings(
            self.data.get('installations', []),
            intersect_default=self.default_installations
        )


class Settings(BaseSettings):

    def __init__(self, data=None):
        super(Settings, self).__init__(self.default_data)
        if data:
            self.data.update(data)

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
        return DictSettings(
            EnvironmentSettings,
            self.data['environments'],
            default_installations=self.installations
        )

    @property
    def installations(self):
        return ListDictSettings(self.data.get('installations', []))


class YAMLSettingsReader(object):
    def __init__(self, configuration_class=Settings):
        self.configuration_class = configuration_class

    def from_file(self, filepath, *args, **kwargs):
        return self.from_yaml(open(filepath), *args, **kwargs)

    def from_yaml(self, yamldata, *args, **kwargs):
        return self.configuration_class(yaml.load(yamldata), *args, **kwargs)


class YAMLSettingsWriter(object):
    def __init__(self, configuration=None):
        if configuration is None:
            configuration = Settings()
        self.configuration = configuration

    def save_to_file(self, filepath):
        yaml.dump(self.configuration.data, open(filepath, 'w+'))
