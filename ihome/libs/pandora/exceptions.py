from requests.structures import CaseInsensitiveDict
class RequestError(Exception):
    def __init__(self, status, headers, body):
        self.status = status
        self.request_id = headers.get('X-ReqId')
        self.message = body

    def __str__(self):
        return str({'status': self.status, 'request_id': self.request_id, 'message': self.message})


def make_exception(resp):
    status = resp.status
    headers = resp.headers
    body = resp.read(4096)
    return RequestError(status, headers, body)
