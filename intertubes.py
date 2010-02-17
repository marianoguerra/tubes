'''some utilities that can be used with tubes'''
import re
import inspect

import tubes

class STag(object):
    '''an object that represents a [x]html tag that closes on definition'''
    def __init__(self, name, **attrs):
        '''constructor

        name -- the name of the tag
        attrs -- attributes for this tag
        '''
        self.name = name
        self.attrs = attrs
        if 'class_' in attrs:
            self.attrs['class'] = attrs['class_']
            del self.attrs['class_']

    def __str__(self):
        '''return a string representation of this tag'''
        attrs = [' %s="%s"' % (key, val) \
                for key, val in self.attrs.iteritems()]
        return "<%s%s />" % (self.name, ' '.join(attrs))

class Tag(STag):
    '''an object that represents a [x]html tag'''
    def __init__(self, name, *childs, **attrs):
        '''constructor

        name -- the name of the tag
        childs -- Tag objects contained inside this tag
        attrs -- attributes for this tag
        '''
        STag.__init__(self, name, **attrs)
        self.childs = list(childs)

    def add(self, *childs):
        '''add childs to the childs list'''
        self.childs += list(childs)

    def __str__(self):
        '''return a string representation of this tag'''
        attrs = [' %s="%s"' % (key, val) \
                for key, val in self.attrs.iteritems()]
        childs = [str(child) for child in self.childs]
        return "<%s%s>%s</%s>" % (self.name, ''.join(attrs),
                '\n'.join(childs), self.name)

def create_tag(name, simple=False):
    '''return a function that builds a tag'''
    if simple:
        return lambda **attrs: STag(name, **attrs)
    else:
        return lambda *childs, **attrs: Tag(name, *childs, **attrs)

TAGS = ('html', 'head', 'title', 'body', 'script', 'h1', 'h2', 'h3', 'h4',
        'h5', 'h6', 'a', 'div', 'span', 'input', 'table', 'th', 'tr', 'td',
        'tbody', 'thead', 'tfooter', 'em', 'strong', 'ol', 'ul', 'li', 'p',
        'address', 'abbr', 'acronym', 'button', 'caption', 'center', 'cite',
        'form', 'frame', 'iframe', 'select', 'option', 'style', 'sup')

STAGS = ('meta', 'link', 'img', 'br', 'hr', 'base')

for tagname in TAGS:
    globals()[tagname] = create_tag(tagname)

for tagname in STAGS:
    globals()[tagname] = create_tag(tagname, True)

def css(path):
    '''return a Tag object to link to a css stylesheet'''
    return link(rel="stylesheet", type="text/css", href=path)

def inline_css(content):
    '''return a Tag object that contains css style'''
    return style(content, type="text/css")

def javascript(path=None, content=None):
    '''return a Tag object that contains or links to js'''
    if path is not None:
        return script(type="text/javascript", src=path)
    else:
        return script(content, type="text/javascript")

def generate_model(classes, namespace='model', initialize_namespace=True):
    code = ''

    if initialize_namespace:
        code += 'var %s = {}\n\n' % (namespace, )

    for class_ in classes:
        code += class_constructor(class_)

    return code

def class_constructor(class_, namespace='model'):
    '''return the constructor of a class in js'''
    args = inspect.getargspec(class_.__init__)
    def_offset = len(args[3])
    common = args[0][1: -def_offset]
    defaults = args[0][-def_offset:]
    first = True

    code = '%s.%s = function (%s) {\n    return {' % (namespace,
            class_.__name__, ', '.join(args[0][1:]))

    for arg in common:
        if first:
            first = False
        else:
            code += '        '

        code += '"%s": %s,\n' % (arg, arg)

    for arg, value in zip(defaults, args[3]):
        if value is None:
            rep = 'null'
        elif value == True or value == False:
            rep = repr(value).lower()
        else:
            rep = repr(value)

        if first:
            first = False
        else:
            code += '        '


        code += '"%s": %s || %s,\n' % (arg, arg, rep)

    code = code[:-2]

    code += '};\n};\n\n'
    return code

def generate_api_test(routes):
    '''generate the html to test the API'''
    wrapper = div(class_='wrapper')
    for method in routes:
        for route in routes[method]:
            name = tubes.underscores_to_camelcase(route.handler.__name__)
            output_id = name + '-output'
            args = []
            start_arg = 1

            if route.accepts == tubes.JSON:
                start_arg = 2

            tbl = table(class_='api-form', id=name)
            output = div(class_='output', id=output_id,
                    onclick="$(this).html('');")
            wrapper.add(div(h2(name), tbl, output, class_='api'))

            for arg in inspect.getargspec(route.handler)[0][start_arg:]:
                argname = name + '-' + arg
                args.append(argname)
                tbl.add(tr(
                    td(arg, class_='left'),
                    td(input(type='text', id=argname, class_='value'),
                        class_='right')))

            if route.has_payload or route.accepts == tubes.JSON:
                tbl.add(tr(
                    td("payload (eval)", class_='left'),
                    td(input(type='text', id=name + '--payload', class_='value'),
                        class_='right')))

            ids = ', '.join("'%s'" % (arg, ) for arg in args)
            tbl.add(tr(td(), td(button('send',
                onclick='sendForm(\'' + name + '\', [' + ids + '], \'' + \
                        output_id + '\')'))))

    return str(wrapper)

def generate_html_example(handler, js_paths=None,
    jquery_path='/files/jquery-1.3.2.js',
    requests_path='requests.js', namespace='requests'):
    '''return a html file that will make use of the
    API defined on routes
    '''
    routes = handler.routes
    head_tag = head(title('API test'), inline_css(EXAMPLE_CSS),
        javascript(path=jquery_path),
        javascript(path=requests_path),
        javascript(content=EXAMPLE_JS % (namespace, )))

    if js_paths is not None:
        for js_path in js_paths:
            head_tag.add(javascript(path=js_path))

    return str(html(head_tag, body(h1('API test'), generate_api_test(routes))))

def generate_requests(handler, namespace='requests'):
    '''return javascript code to interact with this handler'''
    def get_rest_call(method, route):
        '''return a string representing a asynchornous REST call'''
        pattern = route.pattern
        if pattern.startswith('^'):
            pattern = pattern[1:]

        if pattern.endswith('?'):
            pattern = pattern[:-1]

        start_arg = 1

        if route.accepts == tubes.JSON:
            start_arg = 2

        parts = re.split('(\(.*?\))', pattern)
        result = ['"']
        args = inspect.getargspec(route.handler)[0][start_arg:]

        for part in parts:
            if part.startswith('('):
                result.append('" + ' + args.pop(0) + ' + "')
            else:
                result.append(part.replace('^', '').replace('$',
                    '').replace('?', ''))

        result.append('"')
        code  = "    var url = %s;\n" % (''.join(result), )
        code += "    $.ajax({'contentType': '%s',\n" % (route.produces, )

        if route.accepts == tubes.JSON:
            code += "        'data': JSON.stringify(data),\n"
        elif route.accepts is not None:
            code += "        'data': data,\n"

        code += "        'dataType': '%s',\n" % \
                (tubes.JQUERY_TYPES.get(route.produces, 'text'),)
        code += "        'error': onError,\n"
        code += "        'success': onSuccess,\n"
        code += "        'type': '%s',\n" % (method, )
        code += "        'url': url});\n"

        return code

    code  = 'var %s = {};\n\n' % (namespace,)
    code += '%s.cb = function(response) {console.log(response);};\n\n' % \
            (namespace, )

    for method, routes in handler.routes.iteritems():
        for route in routes:
            start_arg = 1

            if route.accepts == tubes.JSON:
                start_arg = 2

            args = inspect.getargspec(route.handler)[0][start_arg:]

            if route.has_payload or route.accepts == tubes.JSON:
                args += ['data']

            args += ['onSuccess', 'onError']
            method_name = tubes.underscores_to_camelcase(route.handler.__name__)

            code += '// handle %s on %s\n' % (method, route.pattern)
            code += '%s.%s = function(%s) {\n%s};\n\n' % (namespace,
                    method_name, ', '.join(args), get_rest_call(method, route))

    return code

EXAMPLE_CSS = """
html, body, div, span{
 border: 0;
 padding: 0;
}

html, body{
 width: 100%;
 height: 100%;
}

body{
 color: #ccc;
 font-family: arial;
 background-color: #111;
}

table, tr, td {
 margin: 2px;
 padding: 2px;
}

h1{
 font-size: 5em;
 color: #369;
 text-align: right;
 margin-right: 15%;
}

.api{
 margin: 1%;
 padding: 1%;
 display: table;
 width: 70%;
 margin-left: 15%;
 border-bottom: 1px solid #555;
}

.api-form{
 width: 100%;
}

.api-form input{
 width: 80%;
 float: right;
}

.output{
 cursor: pointer;
 text-align: center;
}

.api-form button {
 float: right;
}
"""

EXAMPLE_JS = """
var reqs = %s;

function sendForm(name, ids, outputId) {
    var values = [], payload, value, func = reqs[name];

    for(id in ids) {
        values.push($('#' + name + ' #' + ids[id]).val());
    }

    payload = $('#' + name + '--payload').val();

    if(typeof(payload) !== 'undefined') {
        value = eval(payload);
        values.push(value);
    }

    values.push(function(response) {onSuccess(outputId, response);});
    values.push(function(response) {onError(outputId, response);});

    func.apply(func, values);
}

function onSuccess(outputId, response) {
    if(typeof(response) === 'string') {
        $('#' + outputId).html(response);
    }
    else {
        $('#' + outputId).html(JSON.stringify(response));
    }

    console.log(response);
}

function onError(outputId, response) {
    $('#' + outputId).html('error: ' + response.responseText);
    console.log(response);
}
"""
