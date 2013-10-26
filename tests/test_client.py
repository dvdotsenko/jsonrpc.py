import json
import time

from unittest import TestCase

from jsonrpcparts import Client, JSONRPC20Serializer, errors

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

