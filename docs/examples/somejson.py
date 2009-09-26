import tubes
# this module generates code for us (you can ignore it if you want)
import intertubes

# decorator to allow python<->json<->javascript
@tubes.JsonClass()
class User(object):
    """a class that represents an user"""

    def __init__(self, user=None, mail=None, firstname=None,
            lastname=None, website=None):
        """constructor"""
        self.user = user
        self.mail = mail
        self.firstname = firstname
        self.lastname = lastname
        self.website = website

handler = tubes.Handler()
# if the path starts with /files serve
# as static files from the files/ directory
handler.register_static_path('/files', 'files/')

# a dict to simulate a database
USERS = {}

# when a post is made to this url the body is extracted and procesed by running
# the User.from_json method, that way we receive a User object
@handler.post('^/user/?$', accepts=tubes.JSON, transform_body=User.from_json)
def new_user(handler, user):
    # add the new user
    USERS[user.user] = user

# update user
@handler.put('^/user/?$', accepts=tubes.JSON, transform_body=User.from_json)
def update_user(handler, user):
    if user.user in USERS:
        USERS[user.user] = user
        return tubes.Response("ok", 200)

    return tubes.Response("user not found", 404)

# match a valid username identifier
# if no produces keyword is given assume JSON
@handler.get('^/user/([a-z][a-zA-Z0-9\.]*)/?')
def get_user(handler, username):
    if username in USERS:
        return USERS[username]

    return tubes.Response("user not found", 404)

# return all users
@handler.get('^/users/?')
def get_users(handler):
    # isn't this easy?
    return User.from_json_list(USERS.items())

# match a valid username identifier
# if accepts json, then the argument after response is the body
@handler.delete('^/user/([a-z][a-zA-Z0-9\.]*)/?', accepts=tubes.JSON, transform_body=User.from_json)
def remove_user(handler, user, username):
    if username in USERS:
        del USERS[username]
        return tubes.Response("ok", 200)

    return tubes.Response("user not found", 404)

# return the generated requests javascript code on that url
# (on production you should save it to a file)
@handler.get('^/requests.js/?$', produces=tubes.JS)
def requests(request):
    '''return the requests.js file to interact with this API'''
    return tubes.Response(REQUESTS)

# return the generated model javascript code on that url
# (on production you should save it to a file)
@handler.get('^/model.js/?$', produces=tubes.JS)
def model(request):
    '''return the model.js file to interact with this API'''
    return MODEL

# show the API test page here
@handler.get('^/test.html/?$', produces=tubes.HTML)
def test(request):
    '''return a dummy html to play with the API'''
    return TEST_PAGE

REQUESTS = intertubes.generate_requests(handler)
MODEL = intertubes.generate_model([User])
TEST_PAGE = intertubes.generate_html_example(handler,
        ('/files/json2.js', '/model.js'))

tubes.run(handler, use_reloader=True)
