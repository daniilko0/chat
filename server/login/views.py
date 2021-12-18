import json
import re

from aiohttp import web


class Login(web.View):

    """Simple Login user by username"""

    async def get(self):
        username = await self._get_username()
        password = await self._get_password()
        # try:
        #     user = await User.get(
        #         username=username, password=password
        #     )  # получить пользователя по юзернейму из БД
        # except DoesNotExist:
        #     return web.Response(
        #         text=json.dumps(
        #             {
        #                 "action": "authorize",
        #                 "status": "error",
        #                 "error": "User not found",
        #             }
        #         ),
        #         status=404,
        #     )
        # else:
        # return web.Response(
        #     text=json.dumps(
        #         {"action": "authorize", "status": "success", "user": username}
        #     )
        # )
        return web.Response(
            body=json.dumps(
                {"action": "authorize", "status": "success", "user": username}
            ),
            content_type="application/json",
        )

    async def _get_username(self):
        """Получает юзернейм и проверяет валидность"""
        data = await self.request.json()
        username = data.get("username", "")
        if not re.match(r"^[a-z]\w{0,9}$", username):
            return False
        return username

    async def _get_password(self):
        data = await self.request.json()
        password = data.get("password")
        return password
