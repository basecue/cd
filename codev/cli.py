import click
from functools import wraps

from .configuration import YAMLConfigurationReader
from .executors import Control, Perform
from .debug import DebugConfiguration


def configuration_option(f):
    def callback(ctx, param, value):
        configuration = YAMLConfigurationReader().from_file(value)
        return configuration

    return click.option('-c', '--configuration',
                        default='.codev',
                        help='Path to configuration file.',
                        callback=callback)(f)


def deployment_option(f):
    @wraps(f)
    def deployment_wrapper(*args, **kwargs):
        deployment = kwargs.pop('deployment')
        kwargs.update(dict(
            environment=deployment[0],
            infrastructure=deployment[1],
            installation=deployment[2]
        ))
        return f(*args, **kwargs)

    return click.option('-d', '--deployment',
                        required=True,
                        is_eager=True,
                        nargs=3,
                        help='environment infrastructure installation')(deployment_wrapper)


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
    def executor_wrapper(configuration, environment, infrastructure, installation, perform, **kwargs):
        if perform:
            executor_class = Perform
        else:
            executor_class = Control

        executor = executor_class(configuration, environment, infrastructure, installation)
        return f(executor=executor, **kwargs)

    return click.option('--perform',
                        is_flag=True,
                        help='Perform mode')(executor_wrapper)


def control_execution(func):
    @wraps(func)
    def control_execution_wrapper(configuration, environment, infrastructure, installation, **kwargs):
        executor = Control(configuration, environment, infrastructure, installation)
        return func(executor, **kwargs)
    return control_execution_wrapper


def nice_exception(func):
    @wraps(func)
    def nice_exception_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if DebugConfiguration.configuration.show_client_exception:
                raise
            if issubclass(type(e), click.ClickException) or issubclass(type(e), RuntimeError):
                raise
            raise click.ClickException(e)
    return nice_exception_wrapper


def debug_option(func):
    @wraps(func)
    def debug_wrapper(debug, **kwargs):
        if debug:
            DebugConfiguration.configuration = YAMLConfigurationReader(DebugConfiguration).from_file(debug)
        return func(**kwargs)

    return click.option('--debug',
                        default=None,
                        help='Path to debug configuration file.')(debug_wrapper)


class execution(object):
    def __init__(self, confirmation=None, control_only=False):
        self.control_only = control_only
        self.confirmation = confirmation

    def __call__(self, func):
        if not self.control_only:
            func = execution_choice(func)
        else:
            func = control_execution(func)

        func = configuration_option(func)
        if self.confirmation:
            func = confirmation_message(self.confirmation)(func)
        func = deployment_option(func)
        func = nice_exception(func)
        func = debug_option(func)
        return func
