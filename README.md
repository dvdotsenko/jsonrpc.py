jsonrpc.py
==========

JSON-RPC tools for Python - serializer, deserializer, request handler decorator - plug your own server

MIT License. Server agnostic. [JSON-RPC v2 support](http://www.jsonrpc.org/specification).

This project is largely a decomposition of [Roland Koebler's original JSON-RPC v.2(preview) Python implementation](http://www.simple-is-better.org/rpc/jsonrpc.py) (and an attempt to move the code to a public repo).

**WORK IN PROGRESS**

The goal of this project is to provide a reliable (as in "say yes to unit-test") JSON-RPC v 1 and 2 implementations of message serialization, deserialization and, a compliant error-trapping, error-formatting wrapper (decorator?) for methods to make error handling transparent).
