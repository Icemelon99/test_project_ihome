import hmac
import hashlib
import base64
from email.utils import formatdate
from . import utils

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse

class Auth(object):
    def __init__(self, access_key, secret_key):
        self.ak = access_key
        self.sk = secret_key.encode('UTF-8')

    def sign_request(self, req):
        req.headers['date'] = formatdate(None, usegmt=True)
        signature = self._do_sign(req)
        signature = signature.decode('UTF-8')
        req.headers['authorization'] = 'Pandora {0}:{1}'.format(self.ak, signature)

    def _do_sign(self, req):
        string_to_sign = self._get_string_to_sign(req)
        string_to_sign = string_to_sign.encode('UTF-8')

        h = hmac.new(self.sk, string_to_sign, hashlib.sha1)
        return base64.urlsafe_b64encode(h.digest())

    def _get_string_to_sign(self, req):
        canonical_headers = self._get_canonical_headers(req)
        path = urlparse(req.url).path
        string_to_sign = '{0}\n{1}\n{2}\n{3}\n{4}{5}'.format(
                req.method,
                utils.get_or_else(req.headers.get('content-md5'), ''),
                utils.get_or_else(req.headers.get('content-type'), ''),
                req.headers.get('date'),
                canonical_headers,
                path)

        return string_to_sign

    def _get_canonical_headers(self, req):
        canon_headers = []
        for k, v in req.headers.items():
            if k.startswith('X-Qiniu-'):
                canon_headers.append((k.lower(), v))

        canon_headers.sort(key=lambda x: x[0])

        canon_headers_string = ''
        for k, v in canon_headers:
            canon_headers_string += '\n{0}:{1}'.format(k, v)

        return canon_headers_string

