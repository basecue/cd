from codev.provisioner import Provisioner
from codev.settings import BaseSettings, SettingsError
from codev.isolator import Isolator


class FabricProvisionerSettings(BaseSettings):
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
            raise SettingsError('Task must be specified for Fabric provisioner.')


class FabricProvisioner(Provisioner):
    provider_name = 'fabric'
    settings_class = FabricProvisionerSettings

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.isolator = Isolator(
            'virtualenv',
            self.performer,
            settings_data=dict(python='2'),
            ident='codev_fabric')

    def install(self):
        # TODO requirements - python-dev, python-virtualenv
        self.isolator.create()
        self.isolator.execute('pip install setuptools')

        version_add = ''
        if self.settings.version:
            version_add = '==%s' % self.settings.version
        self.isolator.execute('pip install --upgrade fabric%s fabtools' % version_add)

    def run(self, machines_groups, info):
        role = self.settings.role or info['environment']

        self.isolator.execute('fab {task} -R {role}'.format(
            task=self.settings.task,
            role=role
        ))

        return True
