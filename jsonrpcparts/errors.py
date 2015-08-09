"""
JSON-RPC (especially v2) prescribes specific error messaging and codes
Here we store the error codes and code that helps us format the errors.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""

#JSON-RPC 2.0 error-codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_METHOD_PARAMS = -32602  #invalid number/type of parameters
INTERNAL_ERROR = -32603  #"all other errors"

#additional error-codes
PROCEDURE_EXCEPTION = -32000
AUTHENTIFICATION_ERROR = -32001
PERMISSION_DENIED = -32002
INVALID_PARAM_VALUES = -32003

#human-readable messages
ERROR_MESSAGE = {
    PARSE_ERROR:"Parse error.",
    INVALID_REQUEST:"Invalid Request.",
    METHOD_NOT_FOUND:"Method not found.",
    INVALID_METHOD_PARAMS:"Invalid parameters.",
    INTERNAL_ERROR:"Internal error.",

    PROCEDURE_EXCEPTION:"Procedure exception.",
    AUTHENTIFICATION_ERROR:"Authentification error.",
    PERMISSION_DENIED:"Permission denied.",
    INVALID_PARAM_VALUES:"Invalid parameter values."
}


class RPCError(Exception):
    """Base class for rpc-errors."""


class RPCFault(RPCError):
    """RPC error/fault package received.

    This exception can also be used as a class, to generate a
    RPC-error/fault message.

    :Variables:
        - error_code:   the RPC error-code
        - error_string: description of the error
        - error_data:   optional additional information
                        (must be json-serializable)
    :TODO: improve __str__
    """

    error_code = None

    def __init__(self, error_data=None, request_id=None, message=None, *args, **kw):
        RPCError.__init__(self, message or ERROR_MESSAGE.get(self.error_code, None), *args, **kw)

        self.error_data = error_data
        self.request_id = request_id

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return( "<RPCFault %s: %s (%s)>" % (self.error_code, repr(self.message), repr(self.error_data)) )


class RPCParseError(RPCFault):
    error_code = PARSE_ERROR


class RPCInvalidRequest(RPCFault):
    error_code = INVALID_REQUEST


class RPCMethodNotFound(RPCFault):
    """Method not found. (METHOD_NOT_FOUND)"""
    error_code = METHOD_NOT_FOUND


class RPCInvalidMethodParams(RPCFault):
    error_code = INVALID_METHOD_PARAMS


class RPCInternalError(RPCFault):
    """Internal error. (INTERNAL_ERROR)"""
    error_code = INTERNAL_ERROR


class RPCProcedureException(RPCFault):
    """Procedure exception. (PROCEDURE_EXCEPTION)"""
    error_code = PROCEDURE_EXCEPTION


class RPCAuthentificationError(RPCFault):
    """AUTHENTIFICATION_ERROR"""
    error_code = AUTHENTIFICATION_ERROR


class RPCPermissionDenied(RPCFault):
    """PERMISSION_DENIED"""
    error_code = PERMISSION_DENIED


class RPCInvalidParamValues(RPCFault):
    """INVALID_PARAM_VALUES"""
    error_code = INVALID_PARAM_VALUES


ERROR_CODE_CLASS_MAP = {
    klass.error_code:klass \
    for klass in [
        RPCParseError,RPCInvalidRequest,RPCMethodNotFound,
        RPCInvalidMethodParams,RPCInternalError,RPCProcedureException,
        RPCAuthentificationError,RPCPermissionDenied,RPCInvalidParamValues
    ]
}

assert len(ERROR_CODE_CLASS_MAP.keys()) == len(ERROR_MESSAGE.keys())
