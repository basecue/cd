import yaml
from .info import VERSION, NAME
from .versioning import Version
from collections import OrderedDict

_mapping_tag = yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG


def dict_representer(dumper, data):
    return dumper.represent_dict(data.iteritems())


def dict_constructor(loader, node):
    return OrderedDict(loader.construct_pairs(node))


yaml.add_representer(OrderedDict, dict_representer)
yaml.add_constructor(_mapping_tag, dict_constructor)


class BadVersion(Exception):
    def __init__(self, version_string):
        self.version_string = version_string


class Configuration(object):
    def load_from_file(self, filepath):
        self.config = yaml.load(file(filepath))
        self.validate()

    def save_to_file(self, filepath):
        yaml.dump(self.config, file(filepath, 'w'))

    def __init__(self):
        self.config = OrderedDict((
            ('version', unicode(VERSION)),
            ('project', self.project_alternative),
            ('infrastructures', []),
            ('environments', [])
        ))

    def validate(self):
        version = Version(VERSION)
        if version <= self.version:
            raise BadVersion(unicode(self.version))

    def default_infrastructure_for_environment(self, environment):
        return 'full'

    def infrastructures_for_environment(self, environment):
        return ['full', 'simple']

    @property
    def version(self):
        return Version(self.config['version'])

    @property
    def environments(self):
        """

        :return: list of environments
        """
        return self.config['environments']

    @property
    def default_environment(self):
        return self.config['environments']['default']

    def project_alternative(self):
        return ''

    @property
    def project(self):
        if 'project' in self.config['project']:
            return self.config['project']

        #TODO SUPPORT FOR git


        raise Exception('Unable to determine project name.')