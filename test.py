import tubes
import intertubes

handler = tubes.Handler()
handler.register_static_path('/docs', 'docs/')

@handler.get('^/ohhai/?$', produces=tubes.TEXT)
def ohhai(request):
    return 'OH HAI!'

@handler.get('^/hello/(.*?)/?$', produces=tubes.TEXT)
def hello(request, name):
    return 'OH HAI! ' + name

@handler.get('^/add/(\\d+)/(\\d+)/?$', produces=tubes.TEXT)
def add(request, first, second):
    return '= ' + str(int(first) + int(second))

@handler.get('^/div/(\\d+)/(\\d+)/?$', produces=tubes.TEXT)
def div(request, first, second):
    if int(second) == 0:
        return tubes.Response('second number can\'t be zero', 500)

    return '= ' + str(float(first) / float(second))

@handler.get('^/json/name/(.+?)/age/(\\d+)/nick/(.+?)/?$')
def json(request, name, age, nick):
    return {'name': name, 'age': age, 'nick': nick}

@handler.get('^/fail/?$', produces=tubes.TEXT)
def fail(request):
    return tubes.Response('nothing to see here, please move along', 404)

@handler.get('^/requests.js/?$', produces=tubes.JS)
def requests(request):
    '''return the requests.js file to interact with this API'''
    return tubes.Response(REQUESTS)

@handler.get('^/test.html/?$', produces=tubes.HTML)
def test(request):
    '''return a dummy html to play with the API'''
    return TEST_PAGE

REQUESTS = handler.to_javascript()
TEST_PAGE = intertubes.generate_html_example(handler.routes)

tubes.run(handler, use_reloader=True, use_debugger=True)
