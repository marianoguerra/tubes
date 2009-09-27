import tubes

handler = tubes.Handler()
handler.register_static_path('/css', 'css/')
handler.register_static_path('/js', 'js/')

@handler.get('^/?$', produces=tubes.HTML)
def main(handler):
    return INDEX

@handler.get('^/favicon.ico$', produces=tubes.ICON)
def get_icon(handler):
    return ICON

INDEX = file('index.html').read()
ICON = file('favicon.ico').read()

if __name__ == '__main__':
    tubes.run_gae(handler)
