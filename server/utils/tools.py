from aiohttp import web


def redirect(request, router_name, *, permanent=False, **kwargs):
    """Перенаправляет на указанный URL"""
    url = request.app.router[router_name].url(**kwargs)
    if permanent:
        raise web.HTTPMovedPermanently(url)
    raise web.HTTPFound(url)
