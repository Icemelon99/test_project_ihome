from . import auth
from . import http
from . import exceptions
from . import utils

class Client(object):
    def __init__(self, endpoint, ak, sk, timeout = 10):
        self.endpoint = endpoint
        self.timeout = timeout
        self.auth = auth.Auth(ak, sk)
        self.session = http.Session()

    def _do_request(self, method, url, data = None, headers = None):
        req = http.Request(method, self.endpoint + url, data, headers)
        self.auth.sign_request(req)

        resp = self.session.do_request(req, timeout=self.timeout)
        if resp.status / 100 != 2:
            raise exceptions.make_exception(resp)

        return resp

    def post_data_from_string(self, repo_name, data):
        url = '/v2/repos/{0}/data'.format(repo_name)
        self._do_request('POST', url, data)

    def post_data(self, repo_name, points):
        data = utils.convert_from(points)
        self.post_data_from_string(repo_name, data)

