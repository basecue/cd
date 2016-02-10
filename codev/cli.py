import click
from functools import wraps

from .configuration import YAMLConfiguration
from .executors import Control, Perform


def configuration_option(f):
    def callback(ctx, param, value):
        configuration = YAMLConfiguration.from_file(value)
        return configuration

    return click.option('-c', '--configuration',
                        default='.codev',
                        help='Path to configuration file.',
                        callback=callback)(f)


def environment_option(f):
    return click.argument('environment')(f)


def infrastructure_option(f):
    return click.argument('infrastructure')(f)


def installation_option(f):
    return click.argument('installation')(f)


def deployment_options(f):
    f = installation_option(f)
    f = infrastructure_option(f)
    f = environment_option(f)
    return f


def confirmation_message(message):
    def decorator(f):
        @wraps(f)
        def confirmation_wrapper(force, **kwargs):
            if not force:
                if not click.confirm(message.format(**kwargs)):
                    raise click.Abort()
            return f(**kwargs)

        return click.option('-f', '--force', is_flag=True,  help='Force')(confirmation_wrapper)

    return decorator


def execution_choice(f):
    @wraps(f)
    def executor_wrapper(configuration, environment, infrastructure, installation, mode, **kwargs):
        executor_class = None
        if mode == 'control':
            executor_class = Control

        elif mode == 'perform':
            executor_class = Perform

        executor = executor_class(configuration, environment, infrastructure, installation)
        return f(executor=executor, **kwargs)

    return click.option('-m', '--mode',
                        type=click.Choice(['control', 'perform']),
                        default='control',
                        help='Mode')(executor_wrapper)


def control_execution(func):
    @wraps(func)
    def wrapper(configuration, environment, infrastructure, installation, **kwargs):
        executor = Control(configuration, environment, infrastructure, installation)
        return func(executor, **kwargs)
    return wrapper


def nice_exception(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        configuration = kwargs.get('configuration')
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if configuration.debug.show_client_exceptions:
                raise
            if issubclass(type(e), click.ClickException) or issubclass(type(e), RuntimeError):
                raise
            raise click.ClickException(e)
    return wrapper


class execution(object):
    def __init__(self, confirmation=None, control_only=False):
        self.control_only = control_only
        self.confirmation = confirmation

    def __call__(self, func):
        if not self.control_only:
            func = execution_choice(func)
        else:
            func = control_execution(func)
        func = deployment_options(func)
        func = configuration_option(func)
        if self.confirmation:
            func = confirmation_message(self.confirmation)(func)

        func = nice_exception(func)
        return func
