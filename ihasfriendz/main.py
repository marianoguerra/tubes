import os
import sys
import time
import json
import uuid
import Queue
from xml.etree import ElementTree

sys.path.append(os.path.abspath('..'))

import tubes
import intertubes
import intertubes as h

import pubsubhubbub_publish as pshb
from feedformatter import Feed


PORT = 8081
DOMAIN = 'http://localhost:' + str(PORT) + '/'

handler = tubes.Handler()
handler.register_static_path('/files', 'files/')

users = {}
notices = {}
user_notices = {}
stream = []
new_notices = Queue.Queue()

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

@tubes.JsonClass()
class Notice(object):
    """a class that represents a notice"""

    def __init__(self, uid=None, title=None, body=None, author=None,
            destination=None, creation=None):
        """constructor, author and destination are User objects
        """
        self.uid = uid
        self.title = title
        self.body = body
        self.author = author
        self.destination = destination

        self.creation = creation
        if self.creation is None:
            self.creation = time.time()

def parse_notices(data):
    """extract notices from an atom feed
    """
    atomns = '{http://www.w3.org/2005/Atom}'
    root = ElementTree.fromstring(data)
    notices = []

    author = root.find(atomns + 'id').text

    for entry in root.findall(atomns + "entry"):
        title = entry.find(atomns + 'title').text
        uid = entry.find(atomns + 'id').text
        body = entry.find(atomns + 'summary').text
        updated = entry.find(atomns + 'updated').text
        # TODO: parse TZ data
        creation = time.strptime(updated[:19], "%Y-%m-%dT%H:%M:%S")

        notice = Notice(uid, title, body, author, None, creation)

        notices.append(notice)

    return notices

def generate_stream_atom(username=None):
    """generate an atom feed from the notices of an user
    """
    feed = Feed()

    if username is None:
        notices = stream
        feed.feed["title"] = "live stream"
        feed.feed["link"] = DOMAIN + "/atom/stream/"
        feed.feed["author"] = DOMAIN
    else:
        notices = user_notices.get(username, None)
        feed.feed["title"] = username + "'s stream"
        feed.feed["link"] = DOMAIN + "/atom/stream/" + username
        feed.feed["author"] = username

    if notices is None:
        return tubes.Response('nothing to see here, please move along', 404)

    for notice in notices:
        item = {}
        item["title"] = notice.title
        item["link"] = DOMAIN + "notice/" + notice.uid
        item["description"] = notice.body
        item["pubDate"] = notice.creation
        item["guid"] = notice.uid

        feed.items.insert(0, item)

    return feed.format_atom_string()

def notice_to_html(notice):
    """return a html object from a notice
    """
    return h.div(
            h.div(h.em(notice.author), ": ", notice.title,
                class_='notice-title'),
            h.div(notice.body, class_='notice-body'), class_='notice')

@handler.get('^/user/([a-zA-Z.]*)/?$', produces=tubes.HTML)
def show_user(request, username):
    div = h.div(class_='user-profile')
    html = h.html(h.head(h.title('user profile')), h.body(div))

    if username in users:
        user = users[username]
        div.add(h.div(username, h.em('(', user.mail, ')'), class_='user'))
        return str(html)

    return tubes.Response('nothing to see here, please move along', 404)

@handler.get('^/users/?$', produces=tubes.HTML)
def show_users(request):
    return json.dumps([user.to_json() for user in users.values()])

@handler.get('^/notice/(.*?)/?$', produces=tubes.HTML)
def show_notice(request, uid):
    if uid in notices:
        notice = notices[uid]
        div = h.div(notice_to_html(notice), id='timeline')
        css = h.css('/files/style.css')
        html = h.html(h.head(h.title('notices'), css), h.body(div))
        return str(html)

    return tubes.Response('nothing to see here, please move along', 404)

@handler.get('^/stream/([a-zA-Z.]*)/?$', produces=tubes.HTML)
def show_stream(request, username):
    if username == '':
        notices = stream
    elif username in user_notices:
        notices = user_notices[username]
    else:
        return tubes.Response('nothing to see here, please move along', 404)

    content = [notice_to_html(notices) for notice in notices]
    css = h.css('/files/style.css')
    html = h.html(h.head(h.title('notices'), css), h.body(*content))

    return str(html)

@handler.get('^/atom/stream/([a-zA-Z.]*)/?$', produces=tubes.ATOM)
def show_stream_atom(request, username):
    if username == '':
        return generate_stream_atom()

    if username in user_notices:
        return generate_stream_atom(username)

    return tubes.Response('nothing to see here, please move along', 404)

@handler.post('^/user/?$', accepts=tubes.JSON, transform_body=User.from_json)
def create_user_json(request, user):
    users[user.user] = user

@handler.post('^/notice/?$', accepts=tubes.JSON, transform_body=Notice.from_json)
def create_notice_json(request, notice):
    notice.uid = str(uuid.uuid4())
    notice.creation = time.time()
    notices[notice.uid] = notice
    stream.append(notice)

    author = notice.author
    if author not in user_notices:
        user_notices[author] = []

    user_notices[author].append(notice)

    pshb.publish('http://localhost:8080/', DOMAIN + "atom/stream/" + author)
    return notice.to_json()

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

@handler.get('^/?$', produces=tubes.HTML)
def index(request):
    '''return the index'''
    return tubes.redirect('/files/index.html', code=302)

@handler.post('^/callback(.*?)$', produces=tubes.HTML)
def receive_notification(request, info):
    data = request.stream.read()

    for notice in parse_notices(data):
        new_notices.put(notice)

@handler.get('^/callback(.*?)$', produces=tubes.TEXT)
def confirm_subscription(request, info):
    if 'hub.challenge' in request.args:
        return request.args['hub.challenge']

    print 'hub.challenge not present in request.args'

@handler.get('^/new-notices/?$', produces=tubes.HTML)
def get_new_notices(request):
    css = h.css('/files/style.css')
    div = h.div(id='timeline')
    html = h.html(h.head(h.title('notices'), css), h.body(div))

    try:
        while True:
            notice = new_notices.get(0, False)
            div.add(notice_to_html(notice))
    except Queue.Empty:
        pass

    return str(html)

REQUESTS = intertubes.generate_requests(handler)
MODEL = intertubes.generate_model([User, Notice])
TEST_PAGE = intertubes.generate_html_example(handler,
        ('/files/json2.js', '/model.js'))

if __name__ == '__main__':
    tubes.run(handler, port=PORT, use_reloader=True, use_debugger=True)
