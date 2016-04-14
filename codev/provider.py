
class ProviderMetaClass(type):
    def __new__(mcs, name, bases, attrs):

        if name == 'Provider':
            return type.__new__(mcs, name, bases, attrs)

        if Provider in bases:
            attrs['providers'] = {}
            cls = type.__new__(mcs, name, bases, attrs)
            cls.provider_class = cls
            return cls
        else:
            for base in bases:
                if hasattr(base, 'provider_class'):
                    attrs['provider_class'] = base.provider_class
                    break
            else:
                raise ImportError("It is unable to determine provider class for class '{name}'.".format(name=name))

            if 'provider_name' in attrs:
                cls = type.__new__(mcs, name, bases, attrs)

                provider_cls = attrs['provider_class']
                provider_name = attrs['provider_name']

                provider_cls.register_provider(provider_name, cls)
                return cls
            else:
                raise ImportError("Attribute 'provider_name' has to be defined in provider class '{name}'.".format(name=name))


class Provider(object, metaclass=ProviderMetaClass):
    @classmethod
    def register_provider(cls, provider_name, provider_cls):
        if provider_name in cls.provider_class.providers:
            # TODO better exception
            raise ImportError(
                "Attribute 'provider_name' with value '{provider_name}' has to be unique for provider classes '{cls_name}' and '{cls_name_conflict}'.".format(
                    provider_name=provider_name,
                    cls_name=provider_cls.__name__,
                    cls_name_conflict=cls.provider_class.providers[provider_name].__name__
                )
            )
        else:
            cls.provider_class.providers[provider_name] = provider_cls

    def __new__(cls, *args, **kwargs):
        if cls == cls.provider_class:
            args_list = list(args)
            provider_name = args_list.pop(0)
            try:
                provider = cls.providers[provider_name]
            except KeyError as e:
                raise ValueError(
                    "Provider '{provider}' does not exist for class '{cls}'.".format(
                        provider=provider_name,
                        cls=cls.__name__
                    )
                )
            return provider(*args_list, **kwargs)
        else:
            return super().__new__(cls)


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
    settings_class = None

    def __init__(self, *args, settings_data=None, **kwargs):
        if self.__class__.settings_class:
            self.settings = self.__class__.settings_class(settings_data)
        super(ConfigurableProvider, self).__init__()
