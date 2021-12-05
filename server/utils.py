import logging
from typing import Tuple, Dict, Union, List, Optional

from aiohttp import web


async def join_room(
    app: web.Application,
    new_room: str,
    old_room: str,
    username: str,
) -> Tuple[Dict[str, Union[str, bool]], bool]:
    """
    Takes a user and changes it's connected room.

    :param app: Application
    :param new_room: New room name
    :param old_room: Old room name
    :param username: Username
    :return: A tuple that contains the dict to return to the end user, as well as
    """
    if not isinstance(new_room, str) or not 3 <= len(new_room) <= 20:
        return (
            {
                "action": "join_room",
                "success": False,
                "message": "Room name must be a string and between 3-20 chars.",
            },
            False,
        )
    if username in app.get("websockets").get(new_room).keys():
        return (
            {
                "action": "join_room",
                "success": False,
                "message": "Name already in use in this room.",
            },
            False,
        )
    app["websockets"][new_room][username] = app["websockets"][old_room].pop(username)
    return {"action": "join_room", "success": True, "message": ""}, True


async def retrieve_users(
    app: web.Application, room: str
) -> Dict[str, Union[str, bool, List[str]]]:
    """
    Takes a room and returns its users
    :param app: Application
    :param room: Room name
    :return: JSON to return to the user
    """
    return {
        "action": "user_list",
        "success": True,
        "room": room,
        "users": list(app["websockets"][room].keys()),
    }


async def broadcast(
    app: web.Application,
    room: str,
    message: dict,
    ignore_users: Optional[List[str]] = None,
) -> None:
    """
    Broadcasts a message to every user in a room. Can specify a user to ignore.

    :param app: Application. From a request, pass `request.app`
    :param room: Room name
    :param message: What to broadcast
    :param ignore_users: Skip broadcast to this user (used for e.g. chat messages)
    :return: None
    """
    for user, ws in app["websockets"][room].items():
        if not ignore_users and user not in ignore_users:
            logging.info("> Sending message %s to %s", message, user)
            await ws.send_json(message)
