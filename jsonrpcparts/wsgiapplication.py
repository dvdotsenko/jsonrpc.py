"""
This module contains code that allows one to have this generic collection
that supports discovery and use of the registered methods.

This file is part of `jsonrpcparts` project. See project's source for license and copyright.
"""
from . import JSONPRCApplication

class JSONPRCWSGIApplication(JSONPRCApplication):

    def handle_wsgi_request(self, environ, start_response):

        assert 'CONTENT_TYPE' in environ
        assert environ['CONTENT_TYPE'] == 'application/json'

        content_length = None
        if 'CONTENT_LENGTH' in environ:
            content_length = environ['CONTENT_LENGTH']
            if content_length:
                content_length = long(content_length)

        input_stream = environ['wsgi.input']

        def get_next_chunk(content_length):
            """Per old WSGI spec, PEP 333, if content length is provided, clients
            are requested to read only that much of input. Reading more than that
            would forever block on old servers.

            Per new WSGI spec, PEP 3333, the input pipe will issue EOF at appropriate time.
            So, there caring about content length is no longer needed for the client,
            but it's still nice to do if content length value is provided.

            Here we reduce the number of the content length remaining by the size of the
            chunk sucked out of the pipe.
            """
            if content_length is None:
                return input_stream.read(), content_length
            else:
                chunk = input_stream.read(content_length)
                return chunk, content_length - len(chunk)

        chunks = []
        chunk, content_length = get_next_chunk(content_length)
        while chunk:
            chunks.append(chunk)
            chunk, content_length = get_next_chunk(content_length)

        request_string = ''.join(chunks)
        response_string = self.handle_request_string(request_string)

        if response_string:
            headers = [
                ('Content-Type', 'application/json'),
                ('Content-Length', len(response_string))
            ]
            start_response('200 OK', headers)
            return [response_string]
        else:
            headers = [
                ('Content-Type', 'text/plain'),
                ('Content-Length', 0)
            ]
            start_response('200 OK', headers)
            return []

    def __call__(self, environ, start_response):
        return self.handle_wsgi_request(environ, start_response)
