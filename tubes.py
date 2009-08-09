'''module to create REST APIS'''
import os
import re
import json
import inspect
from werkzeug import Request
from werkzeug import Response
import werkzeug

# http://www.sfsu.edu/training/mimetype.htm
BIN = 'application/octet-stream'
JSON = 'application/json'
TEXT = 'text/plain'
HTML = 'text/html'
XML = 'text/xml'
JS = 'application/javascript'

JQUERY_TYPES = {}
JQUERY_TYPES[JSON] = 'json'
JQUERY_TYPES[TEXT] = 'text'
JQUERY_TYPES[HTML] = 'html'
JQUERY_TYPES[XML] = 'xml'

class Route(object):
    '''a class that represents a registered route'''
    def __init__(self, pattern, handler, accepts=None, produces='text/plain',
            has_payload=False):
        '''pattern -- the regex that when matches calls handler
        handler -- the method to call when pattern matches
        accepts -- the content type that is accepted
        produces -- the content type that handler produces
        has_payload -- if the request contains information on the body
        '''

        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.group_count = pattern.count('(')
        self.handler = handler
        self.accepts = accepts
        self.produces = produces
        self.has_payload = has_payload

def generate_route_decorator(method):
    '''return a decorator that will add Route objects to method'''
    def decorator(self, pattern, accepts=None, produces=JSON, has_payload=False):
        '''the decorator to register a new Route'''
        def wrapper(func):
            '''the decorator itself'''
            self.register_route(method, pattern, func, accepts, produces,
                    has_payload)
            return func
        return wrapper
    return decorator

class Handler(object):
    '''handler for requests'''
    def __init__(self):
        self.routes = {}
        self.marshallers = {JSON: json.dumps, TEXT: str}
        self.static_paths = {}

    def handle(self, environ, start_response):
        '''try to match the request with the registered routes'''
        path = environ.get('PATH_INFO', '')
        command = environ.get('REQUEST_METHOD', None)
        request = Request(environ)

        for route in self.routes.get(command, ()):
            # TODO: handle accepts
            match = route.regex.match(path)

            if match is not None:
                if route.group_count == 0:
                    result = route.handler(request)
                elif route.group_count == 1:
                    result = route.handler(request, match.group(1))
                else:
                    result = route.handler(request,
                        *match.group(*range(1, route.group_count + 1)))

                if isinstance(result, Response):
                    return result(environ, start_response)

                if route.produces in self.marshallers:
                    result = self.marshallers[route.produces](result)

                return Response(result, content_type=route.produces)(environ,
                        start_response)
        return Response(status=404)(environ, start_response)

    def register_route(self, method, pattern, handler, accepts, produces,
            has_payload):
        '''register a new route on the routes class variable'''
        if method not in self.routes:
            self.routes[method] = []

        self.routes[method].append(Route(pattern, handler, accepts, produces,
            has_payload))

    def register_marshaller(self, mimetype, func):
        '''register a method to transform an input to an output accourding
        to the mimetype '''
        self.marshallers[mimetype] = func

    def register_static_path(self, match_path, *dest_path):
        '''register a path that will be served as static content'''
        self.static_paths[match_path] = os.path.join(*dest_path)

    def to_javascript(self, namespace='requests'):
        '''return javascript code to interact with this handler'''
        def get_rest_call(method, route):
            '''return a string representing a asynchornous REST call'''
            pattern = route.pattern
            if pattern.startswith('^'):
                pattern = pattern[1:]

            if pattern.endswith('?'):
                pattern = pattern[:-1]

            parts = re.split('(\(.*?\))', pattern)
            result = ['"']
            args = inspect.getargspec(route.handler).args[1:]

            for part in parts:
                if part.startswith('('):
                    result.append('" + ' + args.pop(0) + ' + "')
                else:
                    result.append(part.replace('^', '').replace('$',
                        '').replace('?', ''))

            result.append('"')
            code  = "    var url = %s;\n" % (''.join(result), )
            code += "    $.ajax({'contentType': '%s',\n" % (route.produces, )

            if route.has_payload:
                if route.accepts == JSON:
                    code += "        'data': JSON.stringify(data),\n"
                else:
                    code += "        'data': data,\n"

            code += "        'dataType': '%s',\n" % \
                    (JQUERY_TYPES.get(route.produces, 'text'),)
            code += "        'error': onError,\n"
            code += "        'success': onSuccess,\n"
            code += "        'type': '%s',\n" % (method, )
            code += "        'url': url});\n"

            return code

        code  = 'var %s = {};\n\n' % (namespace,)
        code += '%s.cb = function(response) {console.log(response);};\n\n' % \
                (namespace, )

        for method, routes in self.routes.iteritems():
            for route in routes:
                args = inspect.getargspec(route.handler).args[1:]

                if route.has_payload:
                    args += ['data']

                args += ['onSuccess', 'onError']

                code += '// handle %s on %s\n' % (method, route.pattern)
                code += '%s.%s = function(%s) {\n%s};\n\n' % (namespace,
                        route.handler.__name__,
                        ', '.join(args),
                        get_rest_call(method, route))

        return code

    # http://tools.ietf.org/html/rfc2616#page-51
    get = generate_route_decorator('GET')
    post = generate_route_decorator('POST')
    put = generate_route_decorator('PUT')
    delete = generate_route_decorator('DELETE')
    options = generate_route_decorator('OPTIONS')
    head = generate_route_decorator('HEAD')
    trace = generate_route_decorator('TRACE')
    connect = generate_route_decorator('CONNECT')

def run(handler, host='0.0.0.0', port=8000, use_reloader=False,
        use_debugger=False, use_evalex=True, extra_files=None,
        reloader_interval=1, threaded=False, processes=1, request_handler=None,
        passthrough_errors=False):
    '''create a server instance and run it'''
    werkzeug.run_simple(host, port, handler.handle, use_reloader, use_debugger,
            use_evalex, extra_files, reloader_interval, threaded, processes,
            request_handler, handler.static_paths, passthrough_errors)

