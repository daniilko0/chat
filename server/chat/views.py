import json
import logging
import mimetypes
import uuid
from pathlib import Path

from aiohttp import web
from aiohttp.web_request import FileField
from tortoise.exceptions import DoesNotExist

from database.models import Room, Message, User, Attachment

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
        data = await self.request.post()
        file: FileField = data.get("file")
        payload: dict = json.loads(data.get("payload_json"))

        file_type = payload.get("attachment")
        dir_path = f"assets/{file_type}s"
        Path(dir_path).mkdir(parents=True, exist_ok=True)
        assets_path = Path(dir_path)
        file_uuid = uuid.uuid4().hex
        ext = mimetypes.guess_extension(file.headers.get("Content-Type"))
        file_path = assets_path / f"{file_uuid}{ext}"
        file_path.open("x+b").write(file.file.read())

        attachment = await Attachment.create(
            id=file_uuid,
            type=file_type,
            path=file_path,
        )
        await Message.create(
            room_id=1,
            user=await User.get(username=payload.get("username")),
            attachment=attachment,
        )

        return web.Response()
