"""
In JSON-RPC it makes sense to group all server-side methods for a given
rpc channel into a "collection" that is inspected for supported method
when it comes time to handle a request.

This module contains code that allows one to have this generic collection
that supports discovery and use of the registered methods.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""
import json

from . import errors
from .serializers import JSONRPC20Serializer

class JSONPRCCollection(dict):
    """
    A dictionary-like collection that helps with registration
    and use (calling of) JSON-RPC methods.
    """

    def register_class(self, instance, name=None):
        """Add all functions of a class-instance to the RPC-services.

        All entries of the instance which do not begin with '_' are added.

        :Parameters:
            - myinst: class-instance containing the functions
            - name:   | hierarchical prefix.
                      | If omitted, the functions are added directly.
                      | If given, the functions are added as "name.function".
        :TODO:
            - only add functions and omit attributes?
            - improve hierarchy?
        """
        prefix_name = name or instance.__class__.__name__

        for e in dir(instance):
            if e[0][0] != "_":
                self.register_function(
                    getattr(instance, e),
                    name="%s.%s" % (prefix_name, e)
                )

    def register_function(self, function, name=None):
        """Add a function to the RPC-services.

        :Parameters:
            - function: function to add
            - name:     RPC-name for the function. If omitted/None, the original
                        name of the function is used.
        """
        if name:
            self[name] = function
        else:
            self[function.__name__] = function


class JSONPRCApplication(JSONPRCCollection):

    def __init__(self, data_serializer=JSONRPC20Serializer, *args, **kw):
        """
        :Parameters:
            - data_serializer: a data_structure+serializer-instance
        """
        super(JSONPRCApplication, self).__init__(*args, **kw)
        self._data_serializer = data_serializer

    def process_requests(self, requests):
        """
        Turns a list of request objects into a list of
        response objects.
        """

        ds = self._data_serializer

        responses = []
        for method, params, request_id, error in requests:

            if error: # these are request message validation errors
                if error.request_id: # no ID = Notification. We don't reply
                    responses.append(ds.assemble_error_response(error))
                continue

            if method not in self:
                if request_id:
                    responses.append(ds.assemble_error_response(
                        errors.RPCMethodNotFound(
                            'Method "%s" is not found.' % method,
                            request_id
                        )
                    ))
                continue

            try:
                if isinstance(params, dict):
                    result = self[method](**params)
                else:
                    result = self[method](*params)
                if request_id:
                    responses.append(ds.assemble_response(result, request_id))
            except errors.RPCFault as ex:
                if request_id:
                    responses.append(ds.assemble_error_response(ex))
            except Exception as ex:
                if request_id:
                    responses.append(ds.assemble_error_response(
                        errors.RPCInternalError(
                            'While processing the follwoing message ("%s","%s","%s") ' % (method, params, request_id) +\
                            'encountered the following error message "%s"' % ex.message
                        )
                    ))

        return responses

    def handle_request_string(self, request_string):
        """Handle a RPC-Request.

        :Parameters:
            - request_string: the received rpc-string
        :Returns: the encoded (serialized as string) JSON of the response
        """

        ds = self._data_serializer

        try:
            requests, is_batch_mode = ds.parse_request(request_string)
        except errors.RPCFault as ex:
            return json.dumps(ds.assemble_error_response(ex))
        except Exception as ex:
            return json.dumps(ds.assemble_error_response(
                errors.RPCInternalError(
                    'While processing the follwoing message "%s" ' % request_string +\
                    'encountered the following error message "%s"' % ex.message
                )
            ))

        responses = self.process_requests(requests)

        if not responses:
            return None

        try:
            if is_batch_mode:
                return json.dumps(responses)
            else:
                return json.dumps(responses[0])
        except Exception as ex:
            return json.dumps(
                ds.assemble_error_response(
                    errors.RPCInternalError(
                        'While processing the follwoing message "%s" ' % request_string +\
                        'encountered the following error message "%s"' % ex.message
                    )
                )
            )
