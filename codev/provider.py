# Copyright (C) 2016  Jan Češpivo <jan.cespivo@gmail.com>
#
#     This program is free software; you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation; either version 2 of the License, or
#     (at your option) any later version.
#
#     This program is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License along
#     with this program; if not, write to the Free Software Foundation, Inc.,
#     51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


class BaseProviderMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        attrs['providers'] = {}
        if 'provider_class' not in attrs:
            raise AttributeError("Attribute 'provider_class' has to be defined in class '{name}'.".format(name=name))
        return type.__new__(mcs, name, bases, attrs)


class BaseProvider(object, metaclass=BaseProviderMetaClass):
    provider_class = None

    def __new__(cls, provider_name, *args, **kwargs):
        """
        :param provider_name:
        :type provider_name: str
        :param args:
        :param kwargs:
        :return:
        :rtype: cls.provider_class
        """

        try:
            provider = cls.providers[provider_name]
        except KeyError as e:
            raise ValueError(
                "Provider '{provider}' does not exist for class '{cls}'.".format(
                    provider=provider_name,
                    cls=cls.__name__
                )
            )
        return provider(*args, **kwargs)

    @classmethod
    def register(cls, provider_name, provider):
        if not issubclass(provider, cls.provider_class):
            raise ValueError("Class '{provider}' has to be subclass of '{provider_class}'.".format(provider=provider, provider_class=cls.provider_class))
        cls.providers[provider_name] = provider


class ConfigurableProvider(object):
    configuration_class = None

    def __init__(self, configuration_data={}):
        if self.__class__.configuration_class:
            self.configuration = self.__class__.configuration_class(configuration_data)
