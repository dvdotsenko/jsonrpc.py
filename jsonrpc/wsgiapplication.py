"""
This module contains code that allows one to have this generic collection
that supports discovery and use of the registered methods.

"""
from . import JSONPRCApplication

class JSONPRCWSGIApplication(JSONPRCApplication):

    def handle_wsgi_request(self, environ, start_response):

        assert 'CONTENT_TYPE' in environ
        assert environ['CONTENT_TYPE'] == 'application/json'

        input_stream = environ['wsgi.input']
        chunks = []
        chunk = input_stream.read()
        while chunk:
            chunks.append(chunk)
            chunk = input_stream.read()

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