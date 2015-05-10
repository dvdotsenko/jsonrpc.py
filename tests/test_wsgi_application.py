import json
import time

import StringIO

from unittest import TestCase

from jsonrpcparts import JSONRPC20Serializer, errors
from jsonrpcparts.wsgiapplication import JSONPRCWSGIApplication

class MockWSGIEnviron(dict):

    def __init__(self, body=None, headers=[], *args, **kw):
        super(MockWSGIEnviron, self).__init__(*args, **kw)

        if body:
            self['wsgi.input']=StringIO.StringIO(body)
        else:
            self['wsgi.input']=StringIO.StringIO()

        for key, value in headers:
            self[key.upper()] = value

class MockWSGIStartResponse(object):

    def __init__(self):
        self.call_log = []

    def __call__(self, code, headers, errors=None):
        self.call_log.append(
            (code, headers, errors)
        )


class JSONPRCWSGIApplicationTestSuite(TestCase):

    def setUp(self):
        super(JSONPRCWSGIApplicationTestSuite, self).setUp()

        def adder(a, b):
            return a + b

        self.app = JSONPRCWSGIApplication(JSONRPC20Serializer)
        self.app.register_function(adder)

    def test_handle_wsgi_request(self):

        request1 = JSONRPC20Serializer.assemble_request(
            'adder',
            (2, 3)
        )
        request2 = JSONRPC20Serializer.assemble_request(
            'adder',
            (4, 3)
        )
        requests_string = JSONRPC20Serializer.json_dumps([request1, request2])

        environ = MockWSGIEnviron(
            requests_string,
            [
                ('CONTENT_TYPE', 'application/json'),
                ('CONTENT_LENGTH', len(requests_string))
            ]
        )
        start_response = MockWSGIStartResponse()

        response_iterable = self.app(environ, start_response)

        assert response_iterable

        response_string = ''.join(response_iterable)
        responses_data = JSONRPC20Serializer.json_loads(response_string)

        assert len(responses_data) == 2

        response_json = responses_data[0]
        assert 'error' not in response_json
        assert response_json['id'] == request1['id']
        assert response_json['result'] == 5

        response_json = responses_data[1]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 7
