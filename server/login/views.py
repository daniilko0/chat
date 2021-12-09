import re
from datetime import time

from aiohttp import web

from server.utils.tools import redirect


class Login(web.View):

    """Simple Login user by username"""

    @staticmethod
    async def get():
        return {}

    async def post(self):
        """Проверяет юзернейм и логинит"""
        username = await self.is_valid()
        if not username:
            redirect(self.request, "login")
        user = ...  # получить пользователя по юзернейму из БД
        await self.login_user(user)
        redirect(self.request, "login")

    async def login_user(self, user):
        """
        Сохраняет пользователя в сессию и перенаправляет в чат.

        Args:
            user: Имя пользователя
        """
        self.request["session"]["user"] = str(user.id)
        self.request["session"]["time"] = time()
        self.request.match_info["slug"] = "default"
        redirect(self.request, "ws")

    async def is_valid(self):
        """Получает юзернейм и проверяет валидность"""
        data = await self.request.post()
        username = data.get("username", "").lower()
        if not re.match(r"^[a-z]\w{0,9}$", username):
            pass
            return False
        return username
