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
    # return click.option('-e', '--environment',
    #                     help='Environment to install on')(f)


def infrastructure_option(f):
    return click.argument('infrastructure')(f)
    # return click.option('-i', '--infrastructure',
    #                     help='Infrastructure to install with')(f)


def version_option(f):
    return click.argument('version')(f)
    # return click.option('-v', '--version',
    #                     help='Mode')(f)


def deployment_options(f):
    f = version_option(f)
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


def mode_choice(f):
    @wraps(f)
    def executor_wrapper(configuration, environment, infrastructure, version, mode, **kwargs):
        executor_class = None
        if mode == 'control':
            executor_class = Control

        elif mode == 'perform':
            executor_class = Perform

        executor = executor_class(configuration, environment, infrastructure, version)
        return f(executor=executor, **kwargs)

    return click.option('-m', '--mode',
                        type=click.Choice(['control', 'perform']),
                        default='control',
                        help='Mode')(executor_wrapper)


class execution(object):
    def __init__(self, confirmation=None):
        self.confirmation = confirmation

    def __call__(self, func):
        func = mode_choice(func)
        func = deployment_options(func)
        func = configuration_option(func)
        if self.confirmation:
            func = confirmation_message(self.confirmation)(func)
        return func
