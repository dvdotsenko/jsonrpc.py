### What is JSON-RPC Parts (for Python)?

JSON-RPC Parts is a library of composable components one would need to assemble a JSON-RPC server or client.

The parts provided are JSON-RPC message parser and serializer, a generic request handler collection, a WSGI-specific request handler and bits and pieces.

This JSON-RPC Parts collection supports both, JSON-RPC v.1.0 and v.2.0 (including "batch" mode for v.2.0).

The parts are split into separate module files that can be used separately from this collection.

This project is largely a decomposition of [Roland Koebler's original JSON-RPC v.2(preview) Python implementation](http://www.simple-is-better.org/rpc/jsonrpc.py) (and an attempt to move the code to a public repo).

**BETA**
