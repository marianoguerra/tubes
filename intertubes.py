import inspect

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

for name in TAGS:
    globals()[name] = create_tag(name)

for name in STAGS:
    globals()[name] = create_tag(name, True)

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

def generate_api_test(routes):
    '''generate the html to test the API'''
    all = div(class_='wrapper')
    for method in routes:
        for route in routes[method]:
            name = route.handler.__name__
            output_id = name + '-output'
            args = []

            tbl = table(class_='api-form', id=name)
            output = div(class_='output', id=output_id,
                    onclick="$(this).html('');")
            all.add(div(h2(name), tbl, output, class_='api'))

            for arg in inspect.getargspec(route.handler).args[1:]:
                argname = name + '-' + arg
                args.append(argname)
                tbl.add(tr(
                    td(arg, class_='left'),
                    td(input(type='text', id=argname, class_='value'),
                        class_='right')))

            ids = ', '.join("'%s'" % (arg, ) for arg in args)
            tbl.add(tr(td(), td(button('send',
                onclick='sendForm(\'' + name + '\', [' + ids + '], \'' + output_id + '\')'))))

    return str(all)

def generate_html_example(routes,
    jquery_path='http://code.jquery.com/jquery-latest.pack.js',
    requests_path='requests.js', namespace='requests'):
    '''return a html file that will make use of the
    API defined on routes
    '''
    return str(html(
        head(title('API test'), inline_css(EXAMPLE_CSS),
            javascript(path=jquery_path),
            javascript(path=requests_path),
            javascript(content=EXAMPLE_JS % (namespace, ))),
        body(h1('API test'), generate_api_test(routes))))

EXAMPLE_CSS = """
html, body, span, div, h1, h2, h3, h4, h5, h6, table, td, tr{
 margin: 0;
 padding: 0;
}

table, tr, td {
 margin: 2px;
 padding: 2px;
}

h1 {
 text-align: center;
}

body{
 color: #333;
 font-family: Helvetica,Arial,Sans-serif;
 width: 100%;
 height: 100%;
}

.api{
 margin: 1%;
 padding: 1%;
 display: table;
 border: 1px solid #555;
}

.api-form{
}

.api-form input{
 width: 100%;
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
    var values = [], func = reqs[name];

    for(id in ids) {
        values.push($('#' + name + ' #' + ids[id]).val());
    }

    values.push(function(response) {onSuccess(outputId, response);});
    values.push(function(response) {onError(outputId, response);});

    func.apply(func, values);
}

function onSuccess(outputId, response) {
    $('#' + outputId).html(response);
    console.log(response);
}

function onError(outputId, response) {
    $('#' + outputId).html('error: ' + response.responseText);
    console.log(response);
}
"""
