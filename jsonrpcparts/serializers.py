"""
JSON-RPC (especially v2) prescribes that the message format adheres
to a specific format/schema. This module contains code that helps
in serializing data (including errors) into JSON-RPC message format.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""

import json
import random
import time
import uuid

from . import errors

def clean_dict_keys(d):
    """Convert all keys of the dict 'd' to (ascii-)strings.

    :Raises: UnicodeEncodeError
    """
    new_d = {}
    for (k, v) in d.iteritems():
        new_d[str(k)] = v
    return new_d


class BaseJSONRPCSerializer(object):
    """
    Common base class for various json rpc serializers
    Mostly done just for keeping track of common methods and attributes
    (and thus define some sort of internal API/signature for these)
    """

    # these are used in stringify/destringify calls like so:
    # json_data_string = json.dumps(data, cls=json_encoder)
    # and allow users to customize the encoder used, thus allowing
    # support for json-serialization of "odd" types like sets, UUID, models ets.
    # by default it's the default JSONEncoder
    json_decoder = json.JSONDecoder
    json_encoder = json.JSONEncoder

    @classmethod
    def json_dumps(cls, obj, **kwargs):
        """
        A rewrap of json.dumps done for one reason - to inject a custom `cls` kwarg

        :param obj:
        :param kwargs:
        :return:
        :rtype: str
        """
        if 'cls' not in kwargs:
            kwargs['cls'] = cls.json_encoder
        return json.dumps(obj, **kwargs)

    @classmethod
    def json_loads(cls, s, **kwargs):
        """
        A rewrap of json.loads done for one reason - to inject a custom `cls` kwarg

        :param s:
        :param kwargs:
        :return:
        :rtype: dict
        """
        if 'cls' not in kwargs:
            kwargs['cls'] = cls.json_decoder
        return json.loads(s, **kwargs)

    @staticmethod
    def assemble_request(method, *args, **kwargs):
        """serialize JSON-RPC-Request
        """
        raise NotImplemented

    @staticmethod
    def assemble_response(result, *args, **kwargs):
        """serialize a JSON-RPC-Response (without error)
        """
        raise NotImplemented

    @staticmethod
    def parse_request(jsonrpc_message_as_string, *args, **kwargs):
        """We take apart JSON-RPC-formatted message as a string and decompose it
        into a dictionary object, emitting errors if parsing detects issues with
        the format of the message.
        """
        raise NotImplemented

    @staticmethod
    def parse_response(jsonrpc_message_as_string, *args, **kwargs):
        """de-serialize a JSON-RPC Response/error
        """
        raise NotImplemented


#----------------------
# JSON-RPC 1.0

class JSONRPC10Serializer(BaseJSONRPCSerializer):
    """JSON-RPC V1.0 data-structure / serializer

    This implementation is quite liberal in what it accepts: It treats
    missing "params" and "id" in Requests and missing "result"/"error" in
    Responses as empty/null.

    :SeeAlso:   JSON-RPC 1.0 specification
    :TODO:      catch json.dumps not-serializable-exceptions
    """

    @staticmethod
    def assemble_request(method, params=tuple(), id=0):
        """serialize JSON-RPC-Request

        :Parameters:
            - method: the method-name (str/unicode)
            - params: the parameters (list/tuple)
            - id:     if id=None, this results in a Notification
        :Returns:   | {"method": "...", "params": ..., "id": ...}
                    | "method", "params" and "id" are always in this order.
        :Raises:    TypeError if method/params is of wrong type or
                    not JSON-serializable
        """
        if not isinstance(method, (str, unicode)):
            raise TypeError('"method" must be a string (or unicode string).')
        if not isinstance(params, (tuple, list)):
            raise TypeError("params must be a tuple/list.")

        return {
            "method": method,
            "params": params,
            "id": id
        }

    @staticmethod
    def assemble_notification_request(method, params=tuple()):
        """serialize a JSON-RPC-Notification

        :Parameters: see dumps_request
        :Returns:   | {"method": "...", "params": ..., "id": null}
                    | "method", "params" and "id" are always in this order.
        :Raises:    see dumps_request
        """
        if not isinstance(method, (str, unicode)):
            raise TypeError('"method" must be a string (or unicode string).')
        if not isinstance(params, (tuple, list)):
            raise TypeError("params must be a tuple/list.")

        return {
            "method": method,
            "params": params,
            "id": None
        }

    @staticmethod
    def assemble_response(result, id=None):
        """serialize a JSON-RPC-Response (without error)

        :Returns:   | {"result": ..., "error": null, "id": ...}
                    | "result", "error" and "id" are always in this order.
        :Raises:    TypeError if not JSON-serializable
        """
        return {
            "result": result,
            "error": None,
            "id": id
        }

    @staticmethod
    def assemble_error_response(error, id=None):
        """serialize a JSON-RPC-Response-error

        Since JSON-RPC 1.0 does not define an error-object, this uses the
        JSON-RPC 2.0 error-object.

        :Parameters:
            - error: a RPCFault instance
        :Returns:   | {"result": null, "error": {"code": error_code, "message": error_message, "data": error_data}, "id": ...}
                    | "result", "error" and "id" are always in this order, data is omitted if None.
        :Raises:    ValueError if error is not a RPCFault instance,
                    TypeError if not JSON-serializable
        """
        if not isinstance(error, errors.RPCFault):
            raise ValueError("""error must be a RPCFault-instance.""")
        if error.error_data is None:
            return {
                "result": None,
                "error": {
                    "code": error.error_code,
                    "message": error.message
                },
                "id": id
            }
        else:
            return {
                "result": None,
                "error": {
                    "code":error.error_code,
                    "message": error.message,
                    "data": error.error_data
                },
                "id": id
            }

    @classmethod
    def parse_request(cls, jsonrpc_message):
        """We take apart JSON-RPC-formatted message as a string and decompose it
        into a dictionary object, emitting errors if parsing detects issues with
        the format of the message.

        :Returns:   | [method_name, params, id] or [method_name, params]
                    | params is a tuple/list
                    | if id is missing, this is a Notification
        :Raises:    RPCParseError, RPCInvalidRPC, RPCInvalidMethodParams
        """
        try:
            data = cls.json_loads(jsonrpc_message)
        except ValueError, err:
            raise errors.RPCParseError("No valid JSON. (%s)" % str(err))

        if not isinstance(data, dict):
            raise errors.RPCInvalidRPC("No valid RPC-package.")
        if "method" not in data:
            raise errors.RPCInvalidRPC("""Invalid Request, "method" is missing.""")
        if not isinstance(data["method"], (str, unicode)):
            raise errors.RPCInvalidRPC("""Invalid Request, "method" must be a string.""")
        if "id" not in data:
            data["id"] = None #be liberal
        if "params" not in data:
            data["params"] = ()     #be liberal
        if not isinstance(data["params"], (list, tuple)):
            raise errors.RPCInvalidRPC("""Invalid Request, "params" must be an array.""")
        if len(data) != 3:
            raise errors.RPCInvalidRPC("""Invalid Request, additional fields found.""")

        # notification / request
        if data["id"] is None:
            return data["method"], data["params"] #notification
        else:
            return data["method"], data["params"], data["id"] #request

    @classmethod
    def parse_response(cls, jsonrpc_message):
        """de-serialize a JSON-RPC Response/error

        :Returns: | [result, id] for Responses
        :Raises:  | RPCFault+derivates for error-packages/faults, RPCParseError, RPCInvalidRPC
                  | Note that for error-packages which do not match the
                    V2.0-definition, RPCFault(-1, "Error", RECEIVED_ERROR_OBJ)
                    is raised.
        """
        try:
            data = cls.json_loads(jsonrpc_message)
        except ValueError, err:
            raise errors.RPCParseError("No valid JSON. (%s)" % str(err))
        if not isinstance(data, dict):
            raise errors.RPCInvalidRPC("No valid RPC-package.")
        if "id" not in data:
            raise errors.RPCInvalidRPC("""Invalid Response, "id" missing.""")
        if "result" not in data:
            data["result"] = None #be liberal
        if "error" not in data:
            data["error"] = None #be liberal
        if len(data) != 3:
            raise errors.RPCInvalidRPC("""Invalid Response, additional or missing fields.""")

        #error
        if data["error"] is not None:
            if data["result"] is not None:
                raise errors.RPCInvalidRPC("""Invalid Response, one of "result" or "error" must be null.""")
            #v2.0 error-format
            if (
                isinstance(data["error"], dict) and
                "code" in data["error"] and
                "message" in data["error"] and
                (
                    len(data["error"]) == 2 or
                    ("data" in data["error"] and len(data["error"])==3)
                )
            ):
                if "data" not in data["error"]:
                    error_data = None
                else:
                    error_data = data["error"]["data"]

                if data["error"]["code"] == errors.PARSE_ERROR:
                    raise errors.RPCParseError(error_data)
                elif data["error"]["code"] == errors.INVALID_REQUEST:
                    raise errors.RPCInvalidRPC(error_data)
                elif data["error"]["code"] == errors.METHOD_NOT_FOUND:
                    raise errors.RPCMethodNotFound(error_data)
                elif data["error"]["code"] == errors.INVALID_METHOD_PARAMS:
                    raise errors.RPCInvalidMethodParams(error_data)
                elif data["error"]["code"] == errors.INTERNAL_ERROR:
                    raise errors.RPCInternalError(error_data)
                elif data["error"]["code"] == errors.PROCEDURE_EXCEPTION:
                    raise errors.RPCProcedureException(error_data)
                elif data["error"]["code"] == errors.AUTHENTIFICATION_ERROR:
                    raise errors.RPCAuthentificationError(error_data)
                elif data["error"]["code"] == errors.PERMISSION_DENIED:
                    raise errors.RPCPermissionDenied(error_data)
                elif data["error"]["code"] == errors.INVALID_PARAM_VALUES:
                    raise errors.RPCInvalidParamValues(error_data)
                else:
                    raise errors.RPCFault(data["error"]["code"], data["error"]["message"], error_data)
            #other error-format
            else:
                raise errors.RPCFault(-1, "Error", data["error"])
        #result
        else:
            return data["result"], data["id"]

#----------------------
# JSON-RPC 2.0

class JSONRPC20Serializer(BaseJSONRPCSerializer):

    @staticmethod
    def assemble_request(method, params=None, notification=False):
        """serialize JSON-RPC-Request

        :Parameters:
            - method: the method-name (str/unicode)
            - params: the parameters (None/list/tuple/dict)
            - notification: bool
        :Returns:   | {"jsonrpc": "2.0", "method": "...", "params": ..., "id": ...}
                    | "jsonrpc", "method", "params" and "id" are always in this order.
                    | "params" is omitted if empty
        :Raises:    TypeError if method/params is of wrong type or
                    not JSON-serializable
        """

        if not isinstance(method, (str, unicode)):
            raise TypeError('"method" must be a string (or unicode string).')
        if params and not isinstance(params, (tuple, list, dict)):
            raise TypeError("params must be a tuple/list/dict or None.")

        base = {
            "jsonrpc": "2.0",
            "method": method
        }

        if params:
            base["params"] = params

        if not notification:
            base['id'] = str(uuid.uuid4())

        return base

    @staticmethod
    def assemble_response(result, request_id):
        return {
            "jsonrpc": "2.0",
            "result": result,
            "id": request_id
        }

    @staticmethod
    def assemble_error_response(error):

        if not isinstance(error, errors.RPCFault):
            raise ValueError("""error must be a RPCFault-instance.""")

        if error.error_data is None:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code":error.error_code,
                    "message":error.message
                },
                "id": error.request_id
            }
        else:
            return {
                "jsonrpc": "2.0",
                "error": {
                    "code":error.error_code,
                    "message": error.message,
                    "data": error.error_data
                },
                "id": error.request_id
            }

    @classmethod
    def _parse_single_request(cls, request_data):
        """

        :Returns:   | [method_name, params, id]
                    | method (str)
                    | params (tuple/list or dict)
                    | id (str/int/None) (None means this is Notification)
        :Raises:    RPCParseError, RPCInvalidRPC, RPCInvalidMethodParams
        """

        request_id = request_data.get('id', None) # Notifications don't have IDs

        for argument in ['jsonrpc', 'method']:
            if argument not in request_data:
                raise errors.RPCInvalidRequest('argument "%s" missing.' % argument, request_id)
            if not isinstance(request_data[argument], (str, unicode)):
                raise errors.RPCInvalidRequest('value of argument "%s" must be a string.' % argument, request_id)

        if request_data["jsonrpc"] != "2.0":
            raise errors.RPCInvalidRequest('Invalid jsonrpc version.', request_id)

        if "params" in request_data:
            if not isinstance(request_data["params"], (list, tuple, dict)):
                raise errors.RPCInvalidMethodParams(
                    'value of argument "parameter" is of non-supported type %s' % type(request_data["params"]),
                    request_id
                )

        return (
            request_data["method"],
            request_data.get("params", None),
            request_id
        )

    @classmethod
    def _parse_single_request_trap_errors(cls, request_data):
        """Traps exceptions generated by __parse_single_request and
        converts them into values of request_id and error in the
        returned tuple.

        :Returns: (method_name, params_object, request_id, error)
                Where:
                - method_name is a str (or None when error is set)
                - params_object is one of list/tuple/dict/None
                - request_id is long/int/string/None
                - error is an instance of errors.RPCFault subclass or None
        """
        try:
            method, params, request_id = cls._parse_single_request(request_data)
            return method, params, request_id, None
        except errors.RPCFault as ex:
            return None, None, ex.request_id, ex

    @classmethod
    def parse_request(cls, request_string):
        """JSONRPC allows for **batch** requests to be communicated
        as array of dicts. This method parses out each individual
        element in the batch and returns a list of tuples, each
        tuple a result of parsing of each item in the batch.

        :Returns:   | tuple of (results, is_batch_mode_flag)
                    | where:
                    | - results is a tuple describing the request
                    | - Is_batch_mode_flag is a Bool indicating if the
                    |   request came in in batch mode (as array of requests) or not.

        :Raises:    RPCParseError, RPCInvalidRequest
        """
        try:
            batch = cls.json_loads(request_string)
        except ValueError as err:
            raise errors.RPCParseError("No valid JSON. (%s)" % str(err))

        if isinstance(batch, (list, tuple)) and batch:
            # batch is true batch.
            # list of parsed request objects, is_batch_mode_flag
            return [cls._parse_single_request_trap_errors(request) for request in batch], True
        elif isinstance(batch, dict):
            # `batch` is actually single request object
            return [cls._parse_single_request_trap_errors(batch)], False

        raise errors.RPCInvalidRequest("Neither a batch array nor a single request object found in the request.")

    @classmethod
    def _parse_single_response(cls, response_data):
        """de-serialize a JSON-RPC Response/error

        :Returns: | [result, id] for Responses
        :Raises:  | RPCFault+derivates for error-packages/faults, RPCParseError, RPCInvalidRPC
        """

        if not isinstance(response_data, dict):
            raise errors.RPCInvalidRequest("No valid RPC-package.")

        if "id" not in response_data:
            raise errors.RPCInvalidRequest("""Invalid Response, "id" missing.""")

        request_id = response_data['id']

        if "jsonrpc" not in response_data:
            raise errors.RPCInvalidRequest("""Invalid Response, "jsonrpc" missing.""", request_id)
        if not isinstance(response_data["jsonrpc"], (str, unicode)):
            raise errors.RPCInvalidRequest("""Invalid Response, "jsonrpc" must be a string.""")
        if response_data["jsonrpc"] != "2.0":
            raise errors.RPCInvalidRequest("""Invalid jsonrpc version.""", request_id)

        error = response_data.get('error', None)
        result = response_data.get('result', None)

        if error and result:
            raise errors.RPCInvalidRequest("""Invalid Response, only "result" OR "error" allowed.""", request_id)

        if error:
            if not isinstance(error, dict):
                raise errors.RPCInvalidRequest("Invalid Response, invalid error-object.", request_id)

            if not ("code" in error and "message" in error):
                raise errors.RPCInvalidRequest("Invalid Response, invalid error-object.", request_id)

            error_data = error.get("data", None)

            if error['code'] in errors.ERROR_CODE_CLASS_MAP:
                raise errors.ERROR_CODE_CLASS_MAP[error['code']](error_data, request_id)
            else:
                error_object = errors.RPCFault(error_data, request_id)
                error_object.error_code = error['code']
                error_object.message = error['message']
                raise error_object

        return result, request_id

    @classmethod
    def _parse_single_response_trap_errors(cls, response_data):
        try:
            result, request_id = cls._parse_single_response(response_data)
            return result, request_id, None
        except errors.RPCFault as ex:
            return None, ex.request_id, ex

    @classmethod
    def parse_response(cls, response_string):
        """JSONRPC allows for **batch** responses to be communicated
        as arrays of dicts. This method parses out each individual
        element in the batch and returns a list of tuples, each
        tuple a result of parsing of each item in the batch.

        :Returns:   | tuple of (results, is_batch_mode_flag)
                    | where:
                    | - results is a tuple describing the request
                    | - Is_batch_mode_flag is a Bool indicating if the
                    |   request came in in batch mode (as array of requests) or not.

        :Raises:    RPCParseError, RPCInvalidRequest
        """
        try:
            batch = cls.json_loads(response_string)
        except ValueError as err:
            raise errors.RPCParseError("No valid JSON. (%s)" % str(err))

        if isinstance(batch, (list, tuple)) and batch:
            # batch is true batch.
            # list of parsed request objects, is_batch_mode_flag
            return [cls._parse_single_response_trap_errors(response) for response in batch], True
        elif isinstance(batch, dict):
            # `batch` is actually single response object
            return [cls._parse_single_response_trap_errors(batch)], False

        raise errors.RPCParseError("Neither a batch array nor a single response object found in the response.")
