0.3.7 Pass-through underlying exception's message into `message` field on JSONRPC error

0.3.6 Fix for RPC application and allow overriding JSON serializer

- Feature - allow override JSON Encoder and Decoder by overriding *Serializer class
- Fix RPC application not liking when `params` attribute is not provided

0.3.5 Fixes for RPC client and application

- Fix same-millisecond-generated request_id are identical issue
- Fix some error responses do not echo back request_id value

0.3.4 Enhacements to RPC client

- PyPi package tweaks (0.3.1, 0.3.2, 0.3.3, 0.3.4)
  No functional changes

0.3.0 Enhacements to RPC client

- Added Web RPC Client class that wraps the JSON serialization of the request and communication of it over HTTP.

0.2.0 Initial Release
