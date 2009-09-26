import tubes

handler = tubes.Handler()

@handler.get("^.*$", produces=tubes.HTML)
def hello_world(handler):
    return "hello world!"

tubes.run(handler)
