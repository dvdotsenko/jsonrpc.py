import datetime
import json
import time
import uuid

from unittest import TestCase

from jsonrpcparts import JSONPRCApplication, JSONRPC20Serializer, errors

class JSONPRCApplicationTestSuite(TestCase):

    def setUp(self):
        super(JSONPRCApplicationTestSuite, self).setUp()

        def adder(a, b):
            return a + b

        class MyTestException(Exception):
            pass

        def blow_up(*args, **kwargs):
            raise MyTestException('Blowing up on command')

        self.app = JSONPRCApplication(JSONRPC20Serializer)
        self.app.register_function(adder)
        self.app.register_function(blow_up)

    def test_process_requests(self):

        request1 = JSONRPC20Serializer.assemble_request(
            'adder',
            (2, 3)
        )
        request2 = JSONRPC20Serializer.assemble_request(
            'adder',
            (4, 3)
        )

        assert request1['id'] != request2['id']

        requests, is_batch_mode = JSONRPC20Serializer.parse_request(
            JSONRPC20Serializer.json_dumps([request1, request2])
        )

        responses = self.app.process_requests(requests)

        assert len(responses) == 2

        response_json = responses[0]
        assert 'error' not in response_json
        assert response_json['id'] == request1['id']
        assert response_json['result'] == 5

        response_json = responses[1]
        assert 'error' not in response_json
        assert response_json['id'] == request2['id']
        assert response_json['result'] == 7

    def test_process_requests_with_errors(self):

        request1 = JSONRPC20Serializer.assemble_request(
            'blow_up',
            (2, 3)
        )
        request2 = JSONRPC20Serializer.assemble_request(
            'adder',
            (4, 3)
        )
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(
            JSONRPC20Serializer.json_dumps([request1, request2])
        )

        responses = self.app.process_requests(requests)

        assert len(responses) == 2

        response_json = responses[0]
        assert 'error' in response_json
        assert set(response_json['error'].keys()) == {'code', 'message', 'data'}
        assert response_json['id'] == request1['id']

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
        requests_string = JSONRPC20Serializer.json_dumps([request1, request2])

        response_string = self.app.handle_request_string(requests_string)

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


class JSONPRCApplicationNonStandardJSONEncoderTestSuite(TestCase):

    def test_handle_request_string_non_standard_json_encoder(self):

        some_guid = uuid.uuid4()

        def get_misshaped_objects(*args):
            return [
                {1,2},
                some_guid
            ]

        class MyCustomJSONEncoder(JSONRPC20Serializer.json_encoder):

            def default(self, o):
                if isinstance(o, set):
                    return list(o)
                if isinstance(o, uuid.UUID):
                    return str(o)
                return super(MyCustomJSONEncoder, self).default(o)

        class MyCustomJSONSerializer(JSONRPC20Serializer):

            json_encoder = MyCustomJSONEncoder

        self.app = JSONPRCApplication(MyCustomJSONSerializer)
        self.app.register_function(get_misshaped_objects)

        request = MyCustomJSONSerializer.assemble_request(
            'get_misshaped_objects'
        )
        requests_string = MyCustomJSONSerializer.json_dumps(request)

        response_string = self.app.handle_request_string(requests_string)

        response_json = MyCustomJSONSerializer.json_loads(response_string)

        assert 'error' not in response_json
        assert response_json['id'] == request['id']
        assert response_json['result'] == [
            [1, 2],
            str(some_guid)
        ]

