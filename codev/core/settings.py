import collections
from collections import OrderedDict
from typing import Type, Dict, Any, Optional, TypeVar, Union, Mapping, Sequence, List


class SettingsError(Exception):
    pass


class BaseSettings(object):
    def __init__(self, data: Optional[Dict] = None) -> None:
        if data is None:
            data = {}
        self.data = data

    def __bool__(self) -> bool:
        return bool(self.data)


class HasSettings(object):
    settings_class: Type[BaseSettings] = None

    def __init__(self, *args: Any, settings_data: Optional[Dict] = None, **kwargs: Any) -> None:
        if self.settings_class:
            self.settings = self.settings_class(settings_data)
        else:
            self.settings = None

        super().__init__(*args, **kwargs)


class ProviderSettings(BaseSettings):
    @property
    def provider(self) -> str:
        return self.data.get('provider')

    @property
    def settings_data(self) -> Dict[str, Any]:
        return self.data.get('settings', {})


# FIXME refactorize all from here


class DictSettings(OrderedDict):
    def __init__(self, cls: Type, data: Dict[str, Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()

        for name, itemdata in data.items():
            self[name] = cls(itemdata, *args, **kwargs)


class ListDictSettings(OrderedDict):

    @staticmethod
    def _intersect_default_value(intersect_default: Dict, key: str, value: Any) -> Dict:
        ret_val = intersect_default.get(key, {})
        ret_val.update(value)
        return ret_val

    def __init__(self, data: Union[Mapping, Sequence], intersect_default: Dict = None) -> None:
        if intersect_default is None:
            intersect_default = {}
        super().__init__()

        if isinstance(data, collections.Mapping):
            for key, value in data.items():
                if not (isinstance(value, dict) or isinstance(value, OrderedDict)):
                    raise ValueError('Object {value} must be dictionary.'.format(value=value))
                self[key] = self._intersect_default_value(intersect_default, key, value)

        elif isinstance(data, collections.Sequence):
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
                self[key] = self._intersect_default_value(intersect_default, key, value)
        else:
            raise ValueError('Object {data} must be list or dictionary.'.format(data=data))


class TaskScriptsSettings(BaseSettings):
    @property
    def onstart(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onstart', []))

    @property
    def onsuccess(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onsuccess', []))

    @property
    def onerror(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onerror', []))


class ConfigurationScriptsSettings(BaseSettings):
    @property
    def onstart(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onstart', []))

    @property
    def onsuccess(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onsuccess', []))

    @property
    def onerror(self) -> ListDictSettings:
        return ListDictSettings(self.data.get('onerror', []))
