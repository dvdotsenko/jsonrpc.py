import json
import time

from unittest import TestCase

from jsonrpc import JSONRPC20Serializer, JSONRPC10Serializer, errors

class JSONRPC20SerializerSerializeTestCases(TestCase):

    def test_serialized_request_contains_required_parts(self):

        request = JSONRPC20Serializer.assemble_request('method_name', (1, 'a'))

        self.assertEqual(
            {'jsonrpc', 'method', 'params', 'id'},
            set(request.keys())
        )

        self.assertEqual(
            request['jsonrpc'],
            '2.0'
        )

        self.assertEqual(
            request['method'],
            'method_name'
        )

        self.assertEqual(
            request['params'],
            (1, 'a')
        )

        assert request['id'] # Truethy

    def test_serialized_request_contains_path_through_id(self):

        request = JSONRPC20Serializer.assemble_request(
            'method_name',
            {"arg1":1, "arg2":'a'}
        )

        self.assertEqual(
            request['params'],
            {"arg1":1, "arg2":'a'}
        )

        self.assertIn(
            'id',
            request
        )

        assert request['id']

    def test_serialized_notification_request_contains_required_parts(self):
        """Notification requests are different in one respect - no "id (or "id" is null)
        """

        request = JSONRPC20Serializer.assemble_request(
            'method_name',
            (1, 'a'),
            notification=True
        )

        self.assertEqual(
            {'jsonrpc', 'method', 'params'},
            set(request.keys())
        )

        self.assertEqual(
            request['jsonrpc'],
            '2.0'
        )

        self.assertEqual(
            request['method'],
            'method_name'
        )

        self.assertEqual(
            request['params'],
            (1, 'a')
        )

    def test_assemble_success_response(self):

        response = JSONRPC20Serializer.assemble_response('value', 12345)

        self.assertEqual(
            {'jsonrpc', 'result', 'id'},
            set(response.keys())
        )

        self.assertEqual(
            response['jsonrpc'],
            '2.0'
        )

        self.assertEqual(
            response['result'],
            'value'
        )

        self.assertEqual(
            response['id'],
            12345
        )

    def test_assemble_error_response(self):

        error = errors.RPCMethodNotFound(request_id=12345)

        response = JSONRPC20Serializer.assemble_error_response(error)

        self.assertEqual(
            {'jsonrpc', 'error', 'id'},
            set(response.keys())
        )

        self.assertEqual(
            response['jsonrpc'],
            '2.0'
        )

        self.assertEqual(
            response['id'],
            12345
        )

        error_object = response['error']

        self.assertEqual(
            {'code', 'message'}, #, 'data'},
            set(error_object.keys())
        )

        self.assertEqual(
            error_object['code'],
            errors.METHOD_NOT_FOUND
        )

class BaseParserTestCase(TestCase):

    @staticmethod
    def get_base_request_object(method_name="method_name", params=[1,'a'], notification=False):
        base = {
            'jsonrpc':'2.0',
            'method':method_name,
        }
        if params:
            base['params'] = params
        if not notification:
            base['id'] = long(time.time() * 1000)
        return base

    @staticmethod
    def get_base_response_object(result="value", error=None):
        base = {
            'jsonrpc':'2.0',
            'id':long(time.time())
        }
        if result:
            base['result'] = result
        if error:
            assert isinstance(error, errors.RPCFault)
            base['error'] = {
                'message':error.message,
                'code':error.error_code,
                'data':'error_data'
            }
        return base


class JSONRPC20SerializerParseRequestTestCases(BaseParserTestCase):

    def test_request_parser_detect_batch(self):
        """JSON-RPC v3 requests may come in "batch" mode - multiple request
        objects wrapped into an array. To respond to these correctly
        we need to retain the knowledge of the request coming in as "batch"
        """

        request_string = json.dumps([self.get_base_request_object()])
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)

        assert is_batch_mode

        request_string = json.dumps(self.get_base_request_object())
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)

        assert not is_batch_mode

    def test_request_parser_complains_about_deformed_request_json(self):

        request_string = json.dumps("blah") + '}'
        with self.assertRaises(errors.RPCParseError):
            requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)

        request_string = json.dumps("blah")
        with self.assertRaises(errors.RPCInvalidRequest):
            requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)

        request_string = json.dumps([])
        with self.assertRaises(errors.RPCInvalidRequest):
            requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)

    def test_request_parser_attaches_right_error_to_each_parsed_request(self):

        request_string = json.dumps({})
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)
        assert len(requests)
        method, params, request_id, error = requests[0]
        assert request_id is None
        assert isinstance(error, errors.RPCInvalidRequest)

        request_string = json.dumps([{}])
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)
        assert len(requests)
        method, params, request_id, error = requests[0]
        assert request_id is None
        assert isinstance(error, errors.RPCInvalidRequest)

        request_data = self.get_base_request_object(notification=False)
        request_data.pop('jsonrpc')
        request_string = json.dumps(request_data)
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)
        assert len(requests)
        method, params, request_id, error = requests[0]
        assert request_id == request_data['id']
        assert isinstance(error, errors.RPCInvalidRequest)

        request_data = self.get_base_request_object(notification=False)
        request_data.pop('method')
        request_string = json.dumps(request_data)
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)
        assert len(requests)
        method, params, request_id, error = requests[0]
        assert request_id == request_data['id']
        assert isinstance(error, errors.RPCInvalidRequest)

    def test_request_parser_complains_about_poor_params(self):
        request_data = self.get_base_request_object(params="asdf", notification=False)
        request_string = json.dumps(request_data)
        requests, is_batch_mode = JSONRPC20Serializer.parse_request(request_string)
        assert len(requests)
        method, params, request_id, error = requests[0]
        assert request_id == request_data['id']
        assert isinstance(error, errors.RPCInvalidMethodParams)

    def test_request_parser_success_non_batch(self):

        request_data1 = self.get_base_request_object(notification=False)

        requests, is_batch_mode = JSONRPC20Serializer.parse_request(json.dumps(request_data1))
        assert len(requests)
        assert not is_batch_mode
        method, params, request_id, error = requests[0]
        assert not error
        assert request_id and request_id == request_data1['id']
        assert params and params == request_data1['params']
        assert method and method == request_data1['method']

    def test_request_parser_success_batch(self):

        request_data1 = self.get_base_request_object(notification=False)
        request_data2 = self.get_base_request_object(params={'a':1}, notification=True)

        requests, is_batch_mode = JSONRPC20Serializer.parse_request(json.dumps([
            request_data1,
            request_data2
        ]))
        assert len(requests)
        assert is_batch_mode

        method, params, request_id, error = requests[0]
        assert not error
        assert request_id and request_id == request_data1['id']

        assert params and params == request_data1['params']
        assert method and method == request_data1['method']

        method, params, request_id, error = requests[1]
        assert not error
        assert not request_id
        assert params and params == request_data2['params']
        assert method and method == request_data2['method']


class JSONRPC20SerializerParseResponseTestCases(BaseParserTestCase):

    def test_detect_batch_mode(self):

        responses, is_batch_mode = JSONRPC20Serializer.parse_response(json.dumps(
            self.get_base_response_object()
        ))
        assert not is_batch_mode

        responses, is_batch_mode = JSONRPC20Serializer.parse_response(json.dumps(
            [self.get_base_response_object()]
        ))
        assert is_batch_mode

    def test_response_parser_success_non_batch(self):

        response_data1 = self.get_base_response_object()

        responses, is_batch_mode = JSONRPC20Serializer.parse_response(json.dumps(
            response_data1
        ))
        assert len(responses)
        assert not is_batch_mode
        result, request_id, error = responses[0]
        assert not error
        assert request_id and request_id == response_data1['id']
        assert result and result == response_data1['result']

    def test_response_parser_success_batch(self):

        response_data1 = self.get_base_response_object()
        response_data2 = self.get_base_response_object(result=None, error=errors.RPCMethodNotFound())

        responses, is_batch_mode = JSONRPC20Serializer.parse_response(json.dumps([
            response_data1,
            response_data2
        ]))
        assert len(responses)
        assert is_batch_mode

        result, request_id, error = responses[0]
        assert not error
        assert request_id and request_id == response_data1['id']
        assert result and result == response_data1['result']

        result, request_id, error = responses[1]
        assert error
        assert request_id and request_id == response_data2['id']
        assert not result

    def test_response_parser_complains_about_deformed_json(self):

        response_string = json.dumps("blah") + '}'
        with self.assertRaises(errors.RPCParseError):
            responses, is_batch_mode = JSONRPC20Serializer.parse_response(response_string)

        response_string = json.dumps("blah")
        with self.assertRaises(errors.RPCParseError):
            responses, is_batch_mode = JSONRPC20Serializer.parse_response(response_string)

        response_string = json.dumps([])
        with self.assertRaises(errors.RPCParseError):
            responses, is_batch_mode = JSONRPC20Serializer.parse_response(response_string)

