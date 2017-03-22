from codev.core import BaseSettings, SettingsError
from codev.core import Isolator

from codev.perform.task import Task


class FabricTaskSettings(BaseSettings):
    @property
    def role(self):
        return self.data.get('role', None)

    @property
    def version(self):
        return self.data.get('version', None)

    @property
    def task(self):
        try:
            return self.data['task']
        except KeyError:
            raise SettingsError('Task must be specified for Fabric task.')


class FabricTask(Task):
    provider_name = 'fabric'
    settings_class = FabricTaskSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = Isolator(
            'virtualenv',
            performer=self.performer,
            settings_data=dict(python='2'),
            ident='codev_fabric')

    def prepare(self):
        # TODO requirements - python-dev, python-virtualenv
        self.isolator.create()
        self.isolator.execute('pip install setuptools')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.isolator.execute('pip install --upgrade fabric%s fabtools' % version_add)

    def run(self, infrastructure, status, input_vars):

        self.isolator.execute('fab {task} -R {role}'.format(
            task=self.settings.task,
            role=self.settings.role
        ))

        return True
