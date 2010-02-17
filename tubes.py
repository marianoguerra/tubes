'''module to create REST APIS'''
import os
import re

import functools

try:
    import json
except ImportError:
    import simplejson as json

import werkzeug
from werkzeug import Request
from werkzeug import Response
from werkzeug import redirect

# http://www.sfsu.edu/training/mimetype.htm
BIN  = 'application/octet-stream'
JSON = 'application/json'
TEXT = 'text/plain'
HTML = 'text/html'
XML  = 'text/xml'
JS   = 'application/javascript'
ATOM = 'application/atom+xml'
ICON = 'image/vnd.microsoft.icon'
PDF  = 'application/pdf'
RTF  = 'application/rtf'
PNG  = 'image/png'

JQUERY_TYPES = {}
JQUERY_TYPES[JSON] = 'json'
JQUERY_TYPES[TEXT] = 'text'
JQUERY_TYPES[HTML] = 'html'
JQUERY_TYPES[XML]  = 'xml'

class Route(object):
    '''a class that represents a registered route'''
    def __init__(self, pattern, handler, accepts=None, produces=TEXT,
            has_payload=False, transform_body=None):
        '''pattern -- the regex that when matches calls handler
        handler -- the method to call when pattern matches
        accepts -- the content type that is accepted
        produces -- the content type that handler produces
        has_payload -- if the request contains information on the body
        transform_body -- if accepts is JSON then call the method in this
            attribute and use the returned value as parameter to the method that
            handles the request
        '''

        self.pattern = pattern
        self.regex = re.compile(pattern)
        self.group_count = pattern.count('(')
        self.handler = handler
        self.accepts = accepts
        self.produces = produces
        self.has_payload = has_payload
        self.transform_body = transform_body

def generate_route_decorator(method):
    '''return a decorator that will add Route objects to method'''
    def decorator(self, pattern, accepts=None, produces=JSON, has_payload=False,
            transform_body=None):
        '''the decorator to register a new Route'''
        def wrapper(func):
            '''the decorator itself'''
            self.register_route(method, pattern, func, accepts, produces,
                    has_payload, transform_body)
            return func
        return wrapper
    return decorator

class Handler(object):
    '''handler for requests'''
    __name__ = 'tubes'

    def __init__(self):
        self.routes = {}
        self.marshallers = {JSON: json.dumps}
        self.static_paths = {}

    def __call__(self, environ, start_response):
        '''try to match the request with the registered routes'''
        path = environ.get('PATH_INFO', '')
        command = environ.get('REQUEST_METHOD', None)
        request = Request(environ)

        for route in self.routes.get(command, ()):
            accepts = request.accept_mimetypes.values()
            if route.accepts and request.accept_mimetypes and \
                    route.accepts not in accepts and  '*/*' not in accepts:
                continue

            match = route.regex.match(path)

            if match is not None:
                if route.group_count == 0:
                    args = []
                elif route.group_count == 1:
                    args = [match.group(1)]
                else:
                    args = match.group(*range(1, route.group_count + 1))

                if route.accepts == JSON:
                    data = json.loads(request.stream.read())

                    if route.transform_body is not None:
                        data = route.transform_body(data)

                    # add the body of the request as first parameter
                    args.insert(0, data)

                try:
                    result = route.handler(request, *args)
                except Response, response:
                    return response

                if isinstance(result, werkzeug.BaseResponse):
                    return result(environ, start_response)

                if route.produces == JSON and is_json_class(result):
                    result = result.to_json_str()
                elif route.produces in self.marshallers:
                    result = self.marshallers[route.produces](result)

                return Response(result, content_type=route.produces)(environ,
                        start_response)

        return Response(status=404)(environ, start_response)

    def register_route(self, method, pattern, handler, accepts, produces,
            has_payload, transform_body):
        '''register a new route on the routes class variable'''
        if method not in self.routes:
            self.routes[method] = []

        self.routes[method].append(Route(pattern, handler, accepts, produces,
            has_payload, transform_body))

    def register_marshaller(self, mimetype, func):
        '''register a method to transform an input to an output accourding
        to the mimetype '''
        self.marshallers[mimetype] = func

    def register_static_path(self, match_path, *dest_path):
        '''register a path that will be served as static content'''
        self.static_paths[match_path] = os.path.join(*dest_path)

    def authorize(self, authorize_func):
        '''decorator to validate a request prior to calling the handler
        if the authorize_func returns True, them the function is called
        otherwise 401 is returned
        '''
        def wrapper(func):
            @functools.wraps(func)
            def inner(*args, **kwargs):
                if authorize_func(args[0]):
                    return func(*args, **kwargs)
                else:
                    return Response("unauthorized", 401)

            return inner
        return wrapper

    # http://tools.ietf.org/html/rfc2616#page-51
    get = generate_route_decorator('GET')
    post = generate_route_decorator('POST')
    put = generate_route_decorator('PUT')
    delete = generate_route_decorator('DELETE')
    options = generate_route_decorator('OPTIONS')
    head = generate_route_decorator('HEAD')
    trace = generate_route_decorator('TRACE')
    connect = generate_route_decorator('CONNECT')

class JsonClass(object):
    '''a class decorator to allow transformations to and from JSON
    '''

    def __init__(self, to_ignore=None, from_ignore=None,
            to_transform=None, from_transform=None, exclude_private_fields=True):
        '''constructor

        to_ignore -- a list of attributes to ignore when transforming to json
        from_ignore -- a list of attributes to ignore when transforming form json
        to_transform -- a dict with name atributes as keys and a callable as value
            that will be called with the name and the value of the attr and
            should return the transformed name and value to be used for
            marshaling
        from_transform -- idem to to_trasnform but used with input values to
            transform
        '''
        self.to_ignore = to_ignore

        if self.to_ignore is None:
            self.to_ignore = []

        self.from_ignore = from_ignore

        if self.from_ignore is None:
            self.from_ignore = []

        self.to_transform = to_transform

        if self.to_transform is None:
            self.to_transform = {}

        self.from_transform = from_transform

        if self.from_transform is None:
            self.from_transform = {}

        self.exclude_private_fields = exclude_private_fields

    def __call__(self, cls):
        '''the decorator, add constants to the class:
            * cls.TUBES_JSON_SERIALIZABLE = True
        and class methods:
         * cls.from_json()
         * cls.from_json_str()
        and instance methods:
         * cls.to_json()
         * cls.to_json_str()
        '''
        if hasattr(cls, 'TUBES_JSON_SERIALIZABLE'):
            return cls

        setattr(cls, 'from_json', classmethod(from_json))
        setattr(cls, 'from_json_str', classmethod(from_json_str))
        setattr(cls, 'to_json', to_json)
        setattr(cls, 'to_json_str', to_json_str)
        setattr(cls, 'to_json_list', classmethod(to_json_list))
        setattr(cls, 'to_json_list_str', classmethod(to_json_list_str))
        setattr(cls, 'TUBES_JSON_SERIALIZABLE', True)
        setattr(cls, 'TUBES_TO_IGNORE', self.to_ignore)
        setattr(cls, 'TUBES_FROM_IGNORE', self.from_ignore)
        setattr(cls, 'TUBES_TO_TRANSFORM', self.to_transform)
        setattr(cls, 'TUBES_FROM_TRANSFORM', self.from_transform)
        setattr(cls, 'TUBES_EXCLUDE_PRIVATE_FIELDS',
                self.exclude_private_fields)

        return cls

def is_json_class(cls):
    '''return True if cls is a json class
    '''
    return hasattr(cls, 'TUBES_JSON_SERIALIZABLE')

def from_json(cls, obj):
    '''return a class instance taking the values from the json obj and
    transforming according to from_transform
    '''
    instance = cls()

    for name, value in obj.iteritems():
        if name in cls.TUBES_FROM_IGNORE:
            continue

        if name in cls.TUBES_FROM_TRANSFORM:
            name, value = cls.TUBES_FROM_TRANSFORM[name](name, value)

        if hasattr(instance, name):
            setattr(instance, name, value)

    return instance

def from_json_str(cls, obj_str):
    '''return a class instance taking the values from the json str and
    transforming according to from_transform
    '''
    return cls.from_json(json.loads(obj_str))

def to_json(self):
    '''return a json representation of the object
    '''
    fields = []
    for name, value in vars(self).iteritems():
        if name in self.TUBES_TO_IGNORE:
            continue

        if self.TUBES_EXCLUDE_PRIVATE_FIELDS and name.startswith('_'):
            continue

        if name in self.TUBES_TO_TRANSFORM:
            name, value = self.TUBES_TO_TRANSFORM[name](name, value)

        fields.append((name, value))

    return dict(fields)

def to_json_str(self):
    '''return a json string representation of the object
    '''
    return json.dumps(self.to_json())

def to_json_list(cls, objs):
    '''return a list of json objects of this class
    '''
    return [obj.to_json() for obj in objs]

def to_json_list_str(cls, objs):
    '''return a string representing a list of json objects of this class
    '''
    return json.dumps(cls.to_json_list(objs))

def _replace_underscore_to_camelcase(match):
    '''function used in underscores_to_camelcase to replace the match
    '''
    return match.group(1).upper()

def _replace_camelcase_to_underscore(match):
    '''function used in camelcase_to_underscores to replace the match
    '''
    return "%s_%s" % (match.group(1), match.group(2).lower())

def underscores_to_camelcase(name):
    '''replace all the underscores followed by a a to z letter to camelcase
    '''
    return re.sub('\_([a-z])', _replace_underscore_to_camelcase, name)

def camelcase_to_underscores(name):
    '''replace all the [a-z] followed by [A-Z] to underscores
    when something like a_b_c_d is replaced to aBCD the oposite wont be a_b_c_d
    but a_bC_d
    '''
    return re.sub('([a-z])([A-Z])', _replace_camelcase_to_underscore, name)

def c2u(name, value):
    '''utility function to be used when transforming to or from JSON
    '''
    return camelcase_to_underscores(name), value

def u2c(name, value):
    '''utility function to be used when transforming to or from JSON
    '''
    return underscores_to_camelcase(name), value

def run(handler, host='0.0.0.0', port=8000, use_reloader=False,
        use_debugger=False, use_evalex=True, extra_files=None,
        reloader_interval=1, threaded=False, processes=1, request_handler=None,
        passthrough_errors=False):
    '''create a server instance and run it'''
    werkzeug.run_simple(host, port, handler, use_reloader, use_debugger,
            use_evalex, extra_files, reloader_interval, threaded, processes,
            request_handler, handler.static_paths, passthrough_errors)

def run_gae(handler):
    '''run the application on google app engine'''
    if handler.static_paths:
        from werkzeug.utils import SharedDataMiddleware
        handler = SharedDataMiddleware(handler, handler.static_paths)

    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(handler)

