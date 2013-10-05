import json
import time

from unittest import TestCase

from jsonrpc import JSONPRCApplication, JSONRPC20Serializer, errors

class JSONPRCApplicationTestSuite(TestCase):

    def setUp(self):
        super(JSONPRCApplicationTestSuite, self).setUp()

        def adder(a, b):
            return a + b

        self.app = JSONPRCApplication(JSONRPC20Serializer)
        self.app.register_function(adder)

    def test_process_requests(self):

        request1 = JSONRPC20Serializer.assemble_request(
            'adder',
            (2, 3)
        )
        request2 = JSONRPC20Serializer.assemble_request(
            'adder',
            (4, 3)
        )
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(
            json.dumps([request1, request2])
        )

        responses = self.app.process_requests(requests)

        assert len(responses) == 2

        response_json = responses[0]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 5

        response_json = responses[1]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 7

    def test_handle_request_string(self):

        request1 = JSONRPC20Serializer.assemble_request(
            'adder',
            (2, 3)
        )
        request2 = JSONRPC20Serializer.assemble_request(
            'adder',
            (4, 3)
        )
        requests_string = json.dumps([request1, request2])

        response_string = self.app.handle_request_string(requests_string)

        responses_data = json.loads(response_string)

        assert len(responses_data) == 2

        response_json = responses_data[0]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 5

        response_json = responses_data[1]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 7
