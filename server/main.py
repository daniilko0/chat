import asyncio
import logging

from aiohttp import web, WSCloseCode, WSMessage
from aiohttp.web_request import Request

from database.core import init_db_connection
from server.utils import broadcast, join_room, retrieve_users

ALLOWED_USER_ACTIONS = ["join_room", "send_message", "get_users"]


async def ws_chat(request: Request) -> web.WebSocketResponse:
    current_websocket = web.WebSocketResponse(autoping=True, heartbeat=60)
    is_ready = current_websocket.can_prepare(request)

    if not is_ready:
        await current_websocket.close(code=WSCloseCode.PROTOCOL_ERROR)
    await current_websocket.prepare(request)

    room = "Default"
    user = "User"

    try:
        async for event in current_websocket:
            if isinstance(event, WSMessage):
                if event.type == web.WSMsgType.text:
                    event_json = event.json()
                    action = event_json.get("action")
                    user = event_json.get("username")
                    if action not in ALLOWED_USER_ACTIONS:
                        await current_websocket.send_json(
                            {
                                "action": action,
                                "success": False,
                                "reason": "Not allowed",
                            }
                        )

                    elif action == "join_room":
                        response, success = await join_room(
                            request.app,
                            new_room=event_json.get("room"),
                            old_room=event_json.get("old_room") or room,
                            username=event_json.get("username"),
                        )
                        if not success:
                            logging.error(
                                f"Unable to join room {event_json.get('room')} by {event_json.get('username')}, "
                                f"reason {response.get('message')}"
                            )
                            await current_websocket.send_json(response)
                        else:
                            logging.info(
                                f"User {event_json.get('username')} joined {event_json.get('room')}"
                            )
                            await broadcast(
                                request.app,
                                room=event_json.get("room"),
                                message={
                                    "action": "left_room",
                                    "room": event_json.get("old_room") or room,
                                    "user": event_json.get("username"),
                                },
                            )
                            await broadcast(
                                request.app,
                                room=event_json.get("room"),
                                message={
                                    "action": "joined_room",
                                    "room": event_json.get("room"),
                                    "user": event_json.get("username"),
                                },
                            )
                            room = event_json.get("room")

                    elif action == "get_users":
                        logging.info(
                            f"{event_json.get('room')}: {event_json.get('username')} requested user list",
                        )
                        user_list = await retrieve_users(
                            app=request.app,
                            room=event_json.get("room"),
                        )
                        await current_websocket.send_json(user_list)

                    elif action == "send_message":
                        logging.info(f"{room}: Message: {event_json.get('message')}")
                        await current_websocket.send_json(
                            {
                                "action": "chat_message",
                                "success": True,
                                "message": event_json.get("message"),
                            }
                        )
                        await broadcast(
                            app=request.app,
                            room=room,
                            message={
                                "action": "chat_message",
                                "message": event_json.get("message"),
                                "user": user,
                            },
                        )
    finally:
        if (users := request.app.get("websockets").get(room)) is not None:
            users.pop(user)

            await broadcast(
                request.app,
                room=room,
                message={"action": "left", "room": room, "user": user},
            )

    return current_websocket


def init_app() -> web.Application:
    app = web.Application()
    app["websockets"] = {}
    asyncio.get_event_loop().run_until_complete(init_db_connection())
    app.on_shutdown.append(shutdown)
    app.add_routes([web.get("/", handler=ws_chat)])

    return app


async def shutdown(app):
    for room in app.get("websockets"):
        for ws in app.get("websockets").get(room).values():
            ws.close()

    app.get("websockets").clear()


def main():
    app = init_app()

    host, port = "127.0.0.1", 8080

    logging.info(f"Running server on {host}:{port}")

    web.run_app(app, host=host, port=port)


if __name__ == "__main__":
    main()
