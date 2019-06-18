import requests

import platform
from requests.structures import CaseInsensitiveDict
from . import __version__
from . import exceptions

_USER_AGENT = 'pandora-sdk-python/{0}({1}/{2}/{3};{4})'.format(__version__, platform.system(), platform.release(), platform.machine(), platform.python_version())

connection_pool_size = 20

class Session(object):
    def __init__(self):
        self.session = requests.Session()

        self.session.mount('http://', requests.adapters.HTTPAdapter(pool_connections=connection_pool_size, pool_maxsize=connection_pool_size))
        self.session.mount('https://', requests.adapters.HTTPAdapter(pool_connections=connection_pool_size, pool_maxsize=connection_pool_size))

    def do_request(self, req, timeout):
        try:
            return Response(self.session.request(req.method, req.url,
                                                 data=req.data,
                                                 headers=req.headers,
                                                 stream=True,
                                                 timeout=timeout))
        except requests.RequestException as e:
            raise exceptions.RequestError(e)


class Request(object):
    def __init__(self, method, url,
                 data=None,
                 headers=None):
        self.method = method
        self.url = url
        self.data = data

        if not isinstance(headers, CaseInsensitiveDict):
            self.headers = CaseInsensitiveDict(headers)
        else:
            self.headers = headers

        if 'User-Agent' not in self.headers:
            self.headers['User-Agent'] = _USER_AGENT


_CHUNK_SIZE = 8 * 1024

class Response(object):
    def __init__(self, response):
        self.response = response
        self.status = response.status_code
        self.headers = response.headers

    def read(self, amt=None):
        if amt is None:
            content = b''
            for chunk in self.response.iter_content(_CHUNK_SIZE):
                content += chunk
            return content
        else:
            try:
                return next(self.response.iter_content(amt))
            except StopIteration:
                return b''

    def __iter__(self):
        return self.response.iter_content(_CHUNK_SIZE)


