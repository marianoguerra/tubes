import tubes

handler = tubes.Handler()


@handler.get("^/?$", produces=tubes.HTML)
def hello_world(handler):
    return "hello world!"

# match one or more characters of any type, optionally an ending slash
@handler.get("^/(.+?)/?$", produces=tubes.HTML)
def hello_name(handler, name):
    return "hello " + name

tubes.run(handler)
