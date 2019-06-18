class Field(object):
    def __init__(self, fk, fv):
        self.key = fk
        self.value = fv

    def __str__(self):
        return '{0}={1}'.format(self.key, self.value)

class Point(object):
    def __init__(self, field_list):
        self.field_list = field_list

    def __str__(self):
        return '\t'.join(str(field) for field in self.field_list)

