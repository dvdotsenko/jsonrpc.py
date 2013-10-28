import json
import time
import mock
import requests
from StringIO import StringIO

from unittest import TestCase

from jsonrpcparts import Client, JSONRPC20Serializer, WebClient
from jsonrpcparts.wsgiapplication import JSONPRCWSGIApplication

class ResponseMock(requests.Response):

    def __init__(self, status_code=200, body='', content_type=None):
        super(ResponseMock, self).__init__()
        self.status_code = status_code
        self.raw = StringIO(body)
        self.headers['Content-Type'] = content_type

class JSONPRCClientTestSuite(TestCase):

    def test_client_as_context_manager_for_batch(self):

        with Client(JSONRPC20Serializer) as batch:
            call_id = batch.call('method_name_one', 'a', 'b')
            batch.notify('method_name_two', a='b', c='d')
            requests = batch.get_batched()

        assert len(requests) == 2

        json_data = requests[0]
        assert json_data['method'] == 'method_name_one'
        assert json_data['params'] == ('a', 'b')
        assert 'id' in json_data
        assert json_data['id'] == call_id

        json_data = requests[1]
        assert json_data['method'] == 'method_name_two'
        assert json_data['params'] == {'a':'b', 'c':'d'}
        assert 'id' not in json_data

class JSONPRCWebClientTestSuite(TestCase):

    def setUp(self):
        super(JSONPRCWebClientTestSuite, self).setUp()

        server_app = JSONPRCWSGIApplication()
        server_app['echo'] = lambda a: a

        self.url = 'http://example.com/rpc'
        self.cl = WebClient(self.url)

    def test_client_call(self):

        cl = self.cl

        # mocking out response so we don't need a server
        cl._communicate = lambda request_json, expect_response: {
            'id': request_json.get('id'),
            'result': 'mocked response value'
        }

        assert 'mocked response value' == cl.call('method_name')

    def test_client_notify(self):

        cl = self.cl

        # mocking out response so we don't need a server
        cl._communicate = lambda request_json, expect_response: None

        # notifying is supposed to be ignorant of the answer.
        # Thus, notify returns with None as soon as the message is sent
        assert not cl.notify('method_name', 'a', 'b')

    def test_requests_is_called_correctly_for_notification(self):

        with mock.patch('requests.post', return_value=ResponseMock(200)) as mocked_post:
            self.cl.notify('method_name', 'a', 'b')
            mocked_post.assert_called_once_with(
                self.url,
                data=json.dumps({
                    'method':'method_name',
                    "jsonrpc": "2.0",
                    'params':['a', 'b']
                }),
                headers={'Content-Type': 'application/json'},
            )

    def test_requests_is_called_correctly_for_call(self):

        content_type = 'application/json'
        body = '{"result":"result"}'

        with mock.patch('requests.post', return_value=ResponseMock(200, body, content_type)) as mocked_post:
            result = self.cl.call('method_name', 'a', 'b')

            self.assertEqual(
                mocked_post.call_count,
                1
            )
            args, kw = mocked_post.call_args

            self.assertEqual(
                args[0],
                self.url
            )

            self.assertEqual(
                kw['headers'],
                {'Content-Type': 'application/json'}
            )

            data = json.loads(kw['data'])
            for key, value in {
                'method':'method_name',
                "jsonrpc": "2.0",
                'params':['a', 'b']
            }.items():
                self.assertEqual(
                    data[key],
                    value
                )

            self.assertEqual(
                result,
                'result'
            )
