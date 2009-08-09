'''examples of the tubes microframework'''
import json
import tubes
import intertubes

handler = tubes.Handler()
handler.register_static_path('/docs', 'docs/')
handler.register_static_path('/files', 'files/')

class Person(object):
    '''a test class to generate the js class'''
    def __init__(self, firstname, lastname, age, email=''):
        '''constructor'''
        self.firstname = firstname
        self.lastname = lastname
        self.age = age
        self.email = email

class Task(object):
    '''a test class to generate the the js class'''
    def __init__(self, name, description, tags=None, priority=3):
        '''constructor'''
        self.name = name
        self.description = description
        self.tags = tags
        self.priority = priority

@handler.get('^/ohhai/?$', produces=tubes.TEXT)
def ohhai(request):
    '''just say hi'''
    return 'OH HAI!'

@handler.get('^/hello/(.*?)/?$', produces=tubes.TEXT)
def hello(request, name):
    '''say hi personally'''
    return 'OH HAI! ' + name

@handler.get('^/add/(\\d+)/(\\d+)/?$', produces=tubes.TEXT)
def add(request, first, second):
    '''add two numbers'''
    return '= ' + str(int(first) + int(second))

@handler.get('^/div/(\\d+)/(\\d+)/?$', produces=tubes.TEXT)
def div(request, first, second):
    '''divide two numbers, return error if the second is zero'''
    if int(second) == 0:
        return tubes.Response('second number can\'t be zero', 500)

    return '= ' + str(float(first) / float(second))

@handler.get('^/json/name/(.+?)/age/(\\d+)/nick/(.+?)/?$')
def json_(request, name, age, nick):
    '''encode an object to json'''
    return {'name': name, 'age': age, 'nick': nick}

@handler.get('^/fail/?$', produces=tubes.TEXT)
def fail(request):
    '''epic fail'''
    return tubes.Response('nothing to see here, please move along', 404)

@handler.get('^/requests.js/?$', produces=tubes.JS)
def requests(request):
    '''return the requests.js file to interact with this API'''
    return tubes.Response(REQUESTS)

@handler.get('^/model.js/?$', produces=tubes.JS)
def model(request):
    '''return the model.js file to interact with this API'''
    return MODEL

@handler.get('^/test.html/?$', produces=tubes.HTML)
def test(request):
    '''return a dummy html to play with the API'''
    return TEST_PAGE

@handler.post('^/add/?$', produces=tubes.JSON, has_payload=True)
def add_post(request):
    '''return the sum of two values but using post and payload'''
    body = request.stream.read()
    data = json.loads(body)
    return '= ' + str(data['first'] + data['second'])

@handler.post('^/echo/?$', accepts=tubes.JSON, produces=tubes.JSON, has_payload=True)
def echo(request):
    '''return the sum of two values but using post and payload'''
    body = request.stream.read()
    data = json.loads(body)
    return data

REQUESTS = intertubes.generate_requests(handler)
MODEL = intertubes.generate_model([Person, Task])
TEST_PAGE = intertubes.generate_html_example(handler,
        ('/files/json2.js', '/model.js'))

tubes.run(handler, use_reloader=True, use_debugger=True)
