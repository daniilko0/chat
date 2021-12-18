import logging

from aiohttp import web
from tortoise.exceptions import DoesNotExist

from database.models import Room, Message, User

logging.basicConfig(level="DEBUG")


class Root(web.View):
    @staticmethod
    async def get():
        return web.WebSocketResponse()


class ChatRoom(web.View):

    """Получает имя комнаты и историю сообщений в ней"""

    async def get(self):
        room_name = self.request.match_info["slug"].lower()
        try:
            room: Room = await Room.get(name=room_name)
        except DoesNotExist:
            return web.Response(
                text='{"room": room_name, "error": "Does not exist!"}', status=500
            )
        return web.Response(
            text='{"room": room, "room_messages": {}}'.format(
                await Message.filter(room=room)
            )
        )


class WebSocket(web.View):

    room = None

    async def get(self):
        """Обработка событий"""

        room = await Room.get_or_create(name=self.request.match_info["slug"].lower())
        self.room = room[0]  # Брать из БД

        data = await self.request.json()
        user = data.get("username")

        if data.get("action", "") == "authorize" and "silent" not in data:
            # Сохранить сообщение о присоединении пользователя в БД
            await Message.create(
                user=await User.get(username=user),
                room=self.room.name,
                text=f"Пользователь {user} присоединился",
            )

        if data.get("action", "") == "send_message":
            await Message.create(
                user=await User.get(username=user),
                room_id=self.room.id,
                text=data.get("message", ""),
            )

        return web.Response()

    async def post(self):
        print(await self.request.multipart())
        return web.Response()
