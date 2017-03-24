from os import path
from collections import OrderedDict

import yaml

from codev import __version__

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


class SettingsError(Exception):
    pass


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
    def settings_data(self):
        return self.data.get('settings', {})


class InfrastructureSettings(ProviderSettings):
    @property
    def groups(self):
        return self.data.get('groups', [])


class DictSettings(OrderedDict):
    def __init__(self, cls, data, *args, **kwargs):
        super().__init__()

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
        super().__init__()

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
                        raise ValueError('Object {obj} must have length equal to 1.'.format(obj=obj))
                else:
                    key = obj
                    value = {}
                self[key] = self.__class__._intersect_default_value(intersect_default, key, value)
        else:
            raise ValueError('Object {data} must be list or dictionary.'.format(data=data))


class TaskScriptsSettings(BaseSettings):
    @property
    def onstart(self):
        return ListDictSettings(self.data.get('onstart', []))

    @property
    def onsuccess(self):
        return ListDictSettings(self.data.get('onsuccess', []))

    @property
    def onerror(self):
        return ListDictSettings(self.data.get('onerror', []))


class TaskSettings(ProviderSettings):
    @property
    def scripts(self):
        return TaskScriptsSettings(self.data.get('scripts', {}))


class IsolationScriptsSettings(BaseSettings):
    @property
    def oncreate(self):
        return ListDictSettings(self.data.get('oncreate', []))

    @property
    def onenter(self):
        return ListDictSettings(self.data.get('onenter', []))


class IsolationSettings(ProviderSettings):
    @property
    def loaded_vars(self):
        return {
            var: open(file).read() for var, file in self.data.get('load_vars', {}).items()
        }

    @property
    def connectivity(self):
        return ListDictSettings(self.data.get('connectivity', {}))

    @property
    def scripts(self):
        return IsolationScriptsSettings(self.data.get('scripts', {}))


class ConfigurationScriptsSettings(BaseSettings):
    @property
    def onstart(self):
        return ListDictSettings(self.data.get('onstart', []))

    @property
    def onsuccess(self):
        return ListDictSettings(self.data.get('onsuccess', []))

    @property
    def onerror(self):
        return ListDictSettings(self.data.get('onerror', []))


class BaseConfigurationSettings(BaseSettings):
    @property
    def tasks(self):
        return DictSettings(
            TaskSettings,
            self.data.get('tasks', {})
        )

    @property
    def scripts(self):
        return ConfigurationScriptsSettings(self.data.get('scripts', {}))


class OptionSettings(BaseConfigurationSettings):
    def __init__(self, data, configuration):
        super().__init__(data)
        self._configuration = configuration

    @property
    def tasks(self):
        if 'tasks' in self.data:
            return DictSettings(
                TaskSettings,
                self.data.get('tasks', {})
            )
        else:
            return self._configuration.tasks

    @property
    def scripts(self):
        if 'scripts' in self.data:
            return ConfigurationScriptsSettings(self.data.get('scripts', {}))
        else:
            return self._configuration.scripts

    def __getattr__(self, item):
        return getattr(self._configuration, item)


class ConfigurationSettings(BaseConfigurationSettings):
    def __init__(self, data, default_sources):
        super().__init__(data)
        self.default_sources = default_sources

    @property
    def sources(self):
        return ListDictSettings(
            self.data.get('sources', [])
        )

    @property
    def performer(self):
        return ProviderSettings(self.data.get('performer', {}))

    @property
    def infrastructure(self):
        return DictSettings(InfrastructureSettings, self.data.get('infrastructure', {}))

    @property
    def isolation(self):
        return IsolationSettings(self.data.get('isolation', {}))

    @property
    def options(self):
        return DictSettings(
            OptionSettings,
            self.data['options'],
            self
        )


class Settings(BaseSettings):

    def __init__(self, data=None):
        super().__init__(self.default_data)
        if data:
            self.data.update(data)

    @property
    def default_data(self):
        return OrderedDict((
            ('version', __version__),
            ('project', path.basename(path.abspath(path.curdir))),
            ('configurations', {})
        ))

    @property
    def version(self):
        return self.data['version']

    @property
    def project(self):
        return self.data['project']

    @property
    def configurations(self):
        return DictSettings(
            ConfigurationSettings,
            self.data['configurations'],
            default_sources=self.sources
        )

    @property
    def sources(self):
        return ListDictSettings(self.data.get('sources', []))


class YAMLSettingsReader(object):
    def __init__(self, settings_class=Settings):
        self.settings_class = settings_class

    def from_file(self, filepath, *args, **kwargs):
        with open(filepath) as file:
            return self.from_yaml(file, *args, **kwargs)

    def from_yaml(self, yamldata, *args, **kwargs):
        return self.settings_class(yaml.load(yamldata), *args, **kwargs)


class YAMLSettingsWriter(object):
    def __init__(self, settings=None):
        if settings is None:
            settings = Settings()
        self.settings = settings

    def save_to_file(self, filepath):
        with open(filepath, 'w+') as file:
            yaml.dump(self.settings.data, file)
