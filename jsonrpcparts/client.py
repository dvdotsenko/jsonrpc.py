"""
This module contains code that simplifies the job of JSON-RPC clients.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""
import json

from . import errors

class Client(object):

    def __init__(self, data_serializer):
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
        if args and kw:
            raise ValueError("JSON-RPC method calls allow only either named or positional arguments.")
        if not method:
            raise ValueError("JSON-RPC method call requires a method name.")

        request = self._data_serializer.assemble_request(
            method, args or kw or None
        )

        if self._in_batch_mode:
            self._requests.append(request)
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
