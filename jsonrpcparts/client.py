"""
This module contains code that simplifies the job of JSON-RPC clients.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""
import json
import requests

from . import errors
from . import JSONRPC20Serializer

class Client(object):

    def __init__(self, data_serializer=JSONRPC20Serializer):
        """
        :Parameters:
            - data_serializer: a data_structure+serializer-instance
        """
        self._in_batch_mode = False
        self._requests = []
        self._data_serializer = data_serializer

    # Context manager API
    def __enter__(self):
        self._in_batch_mode = True
        self._requests = []
        return self

    # Context manager API
    def __exit__(self, *args):
        self._in_batch_mode = False
        self._requests = []
        pass

    def call(self, method, *args, **kw):
        """
        In context of a batch we return the request's ID
        else we return the actual json
        """
        if args and kw:
            raise ValueError("JSON-RPC method calls allow only either named or positional arguments.")
        if not method:
            raise ValueError("JSON-RPC method call requires a method name.")

        request = self._data_serializer.assemble_request(
            method, args or kw or None
        )

        if self._in_batch_mode:
            self._requests.append(request)
            return request.get('id')
        else:
            return request

    def notify(self, method, *args, **kw):
        if args and kw:
            raise ValueError("JSON-RPC method calls allow only either named or positional arguments.")
        if not method:
            raise ValueError("JSON-RPC method call requires a method name.")

        request = self._data_serializer.assemble_request(
            method, args or kw or None, notification=True
        )

        if self._in_batch_mode:
            self._requests.append(request)
        else:
            return request

    def get_batched(self):
        if not self._in_batch_mode:
            return []
        else:
            return self._requests

class WebClient(Client):
    """
    This class internalizes the JSON RPC Client class which allows batching of requests
    and adds code that turns RPC call / notification run into HTTP requests.
    """

    def __init__(self, rpc_server_url, data_serializer=JSONRPC20Serializer):
        """
        :Parameters:
            - prc_server_url: string
            - data_serializer: a data_structure+serializer-instance
        """
        super(WebClient, self).__init__(data_serializer)
        self._rpc_server_url = rpc_server_url

    def _communicate(self, request_json, expect_response):
        response = requests.post(
            self._rpc_server_url,
            data=json.dumps(request_json),
            headers={'Content-Type': 'application/json'}
        )

        assert response.status_code == 200
        if expect_response:
            return response.json()

    def notify(self, method, *args, **kw):
        """

        """
        self._communicate(
            super(WebClient, self).notify(method, *args, **kw),
            expect_response=False
        )

    def call(self, method, *args, **kw):
        """
`
        """
        json_rpc_response = self._communicate(
            super(WebClient, self).call(method, *args, **kw),
            expect_response=True
        )

        #base['error'] = {
        #    'message':error.message,
        #    'code':error.error_code,
        #    'data':'error_data'
        #}

        if 'error' in json_rpc_response:
            error_class = errors.ERROR_CODE_CLASS_MAP.get(
                json_rpc_response['error'].get('code')
            ) or errors.RPCError
            if issubclass(error_class, errors.RPCFault):
                raise error_class(
                    json_rpc_response['error'].get('data'),
                    json_rpc_response.get('id'),
                    json_rpc_response['error'].get('message')
                )
            else:
                raise error_class(
                    json_rpc_response['error'].get('message')
                )

        return json_rpc_response['result']
