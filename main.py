import tubes

handler = tubes.Handler()
handler.register_static_path('/css', 'css/')
handler.register_static_path('/js', 'js/')

@handler.get('^/?$', produces=tubes.HTML)
def get_user(handler):
    return INDEX

INDEX = file('index.html').read()

if __name__ == '__main__':
    tubes.run_gae(handler)
