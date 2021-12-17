from aiohttp import web, WSMessage

from database.models import Room, Message


class Root(web.View):
    async def get(self):
        return web.Response(text="Hello world!")


class ChatRoom(web.View):

    """Получает имя комнаты и историю сообщений в ней"""

    async def get(self):
        room: Room = await Room.get(name=self.request.match_info["slug"].lower())
        return {"room": room, "room_messages": await Message.filter(room=room)}


class WebSocket(web.View):

    room = None

    async def broadcast(self, message):
        """
        Отправить сообщение всем в комнате

        Args:
            message: Сообщение

        """
        for peer in self.request.app["wslist"][self.room.id].values():
            peer.send_json(message)

    async def disconnect(self, username, socket, silent=False):
        """
        Отключает пользователя от комнаты

        Args:
            username: Имя пользователя
            socket: Сокет
            silent: Не отправлять сообщение

        """
        self.request.app["wslist"][self.room.id].pop(username)

        if not socket.closed:
            await socket.close()

        if not silent:
            message = ...  # Сохранить сообщение о выходе в БД
            await self.broadcast(message)

    async def get(self):
        """Обработка событий"""
        self.room = ...  # Брать из БД
        user = self.request["user"]
        app = self.request.app

        ws = web.WebSocketResponse()
        await ws.prepare(self.request)
        if self.room.id not in app["wslist"]:
            app["wslist"][self.room.id] = {}

        app["wslist"][self.room.id][user.username] = ws
        message = ...  # Сохранить сообщение о присоединении пользователя в БД

        await self.broadcast(message)

        async for msg in ws:
            if isinstance(msg, WSMessage):
                if msg.type == web.WSMsgType.text:
                    text = msg.data.strip()
                    message = ...  # Сохранить сообщение в БД
                    await self.broadcast(message)

        app["wslist"].pop(user.username)

        message = ...  # Сохранить сообщение о покидании чата в БД
        await self.broadcast(message)

        return ws
