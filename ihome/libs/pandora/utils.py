from . import models

def get_or_else(value, default_value):
    if value is None:
        return default_value
    else:
        return value

def convert_from(points):
    return '\n'.join(str(p) for p in points)

def to_point(fields):
    return '\t'.join('{0}={1}'.format(p[0], escape(str(to_bytes(p[1])))) for p in fields)

def to_bytes(data):
    try:

        if isinstance(data, unicode):
            return data.encode('UTF-8')
    except NameError:

        if isinstance(data, bytes):
            return data.encode('utf-8')

    return data

def escape(s):
    return s.replace('\r', '\\r').replace('\t', '\\t').replace('\n', '\\n').replace('\\', '\\\\')
