import os

from tortoise import Tortoise


async def init_db_connection():
    await Tortoise.init(
        {
            "connections": {"default": os.getenv("DATABASE_URL")},
            "apps": {
                "models": {
                    "models": [
                        "database.models",
                        "aerich.models",
                    ],
                },
            },
        }
    )
    await Tortoise.generate_schemas()
