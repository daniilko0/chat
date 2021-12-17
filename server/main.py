import asyncio
import logging

from aiohttp import web

from database.core import init_db_connection
from server.chat.views import WebSocket, ChatRoom, Root
from server.login.views import Login

logging.basicConfig(level=logging.DEBUG)


async def shutdown(server, app, handler):
    """Выключение сервера."""
    for room in app["wslist"].values():
        for peer in room.values():
            peer.send_json({"text": "Server shutdown"})

    server.close()
    await server.wait_closed()
    await app.shutdown()
    await handler.finish_connections(10.0)
    await app.cleanup()


def create_app() -> web.Application:
    app = web.Application()
    app["wslist"] = {}
    asyncio.get_event_loop().run_until_complete(init_db_connection())
    app.add_routes(
        [
            web.get("/", handler=Root, name="root"),
            web.get("/ws/{slug}", handler=WebSocket, name="ws"),
            web.get("/room/{slug}", handler=ChatRoom, name="get_history"),
            web.get("/login", handler=Login, name="login"),
        ]
    )

    return app


if __name__ == "__main__":
    application = create_app()
    host, port = "127.0.0.1", 8080
    web.run_app(application, host=host, port=port)
