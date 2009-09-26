import tubes

handler = tubes.Handler()

@handler.get("^/?$", produces=tubes.HTML)
def hello_world(handler):
    return "hello world!"

@handler.get("^/fail/?$", produces=tubes.HTML)
def fail(handler):
    return tubes.Response("introductory example fail", 500)

@handler.get("^/not-here/?$", produces=tubes.HTML)
def not_here(handler):
    return tubes.Response("nothing to see here, please move along", 404)

@handler.get("^/redirect/?$", produces=tubes.HTML)
def redirect(handler):
    return tubes.redirect("/", code=301)

# you can make werkzeug reload the server everytime a change is made
# also you can enable a debugger useful when developing to inspect exceptions
# on the browser
tubes.run(handler, use_reloader=True, use_debugger=True)
