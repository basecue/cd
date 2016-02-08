
class BaseProviderMetaClass(type):
    def __new__(mcs, name, bases, attrs):
        attrs['providers'] = {}
        if 'provider_class' not in attrs:
            raise AttributeError("Attribute 'provider_class' has to be defined in class '{name}'.".format(name=name))
        return type.__new__(mcs, name, bases, attrs)


class BaseProvider(object, metaclass=BaseProviderMetaClass):
    provider_class = None

    def __new__(cls, provider_name, *args, **kwargs):
        provider = cls.providers[provider_name]
        return provider(*args, **kwargs)

    @classmethod
    def register(cls, provider_name, provider):
        if not issubclass(provider, cls.provider_class):
            raise ValueError("Class '{provider}' has to be subclass of '{provider_class}'.".format(provider=provider, provider_class=cls.provider_class))
        cls.providers[provider_name] = provider
