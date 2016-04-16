
class ProviderMetaClass(type):
    def __new__(mcs, name, bases, attrs):

        if name == 'Provider':
            return type.__new__(mcs, name, bases, attrs)

        if Provider in bases:
            cls = type.__new__(mcs, name, bases, attrs)
            cls.providers = {}
            cls.provider_class = cls
            if cls.provider_name is not None:
                raise ImportError(
                    "Attribute 'provider_name' has not to be defined in provider class '{name}'.".format(name=name)
                )
            return cls
        else:
            for base in bases:
                if base.provider_class is not None:
                    attrs['provider_class'] = base.provider_class
                    break
            else:
                raise ImportError("It is unable to determine provider class for class '{name}'.".format(name=name))

            if 'provider_name' in attrs:
                if not isinstance(attrs['provider_name'], str):
                    raise TypeError("Attribute 'provider_name' has to be 'str' type in provider class '{name}'.".format(name=name))
                cls = type.__new__(mcs, name, bases, attrs)
                cls.provider_class.register_provider(cls.provider_name, cls)
                return cls
            else:
                raise ImportError("Attribute 'provider_name' has to be defined in provider class '{name}'.".format(name=name))

    def __call__(cls, *args, **kwargs):
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
            return super().__call__(*args, **kwargs)


class Provider(object, metaclass=ProviderMetaClass):
    provider_name = None
    provider_class = None

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


class ConfigurableProvider(object):
    settings_class = None

    def __init__(self, *args, settings_data=None, **kwargs):
        if self.__class__.settings_class:
            self.settings = self.__class__.settings_class(settings_data)
        super().__init__()
