"""
remove?
"""

class Version(object):
    def _split_from_string(self, version_string):
        return version_string.split('.')

    def __init__(self, version_string='0'):
        self.version_parts = self._split_from_string(version_string)

    def change(self, change):
        """
        :param change: ie '0.0.1'
        :return: None
        """
        #TODO

    def __cmp__(self, other):
        comparations = map(lambda x, y: cmp(x, y), self.version_parts, other.version_parts)
        for comparation in comparations:
            if comparation != 0:
                return comparation
        return 0

    def __str__(self):
        return '.'.join(map(str, self.version_parts))

