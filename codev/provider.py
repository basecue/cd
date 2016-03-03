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
        provider.provider_name = provider_name
        cls.providers[provider_name] = provider


class ConfigurableProvider(object):
    configuration_class = None

    def __init__(self, *args, configuration_data={}, **kwargs):
        if self.__class__.configuration_class:
            self.configuration = self.__class__.configuration_class(configuration_data)
        super(ConfigurableProvider, self).__init__(*args, **kwargs)
