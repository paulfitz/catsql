
import re

class Nullify(object):

    def __init__(self):
        self.need_underscore = re.compile(r'^_*NULL$')
        self.has_underscore = re.compile(r'^_(_*NULL)$')
        pass

    def encode_null(self, value):
        if value is None:
            return 'NULL'
        if not isinstance(value, basestring):
            return value
        if self.need_underscore.match(value):
            return '_{}'.format(value)
        return value

    def decode_null(self, value):
        if value is None:
            return value
        if not isinstance(value, basestring):
            return value
        if value == 'NULL':
            return None
        result = self.has_underscore.match(value)
        if result:
            return result.group(1)
        return value
