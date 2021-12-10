import os

from tortoise import Tortoise

CONFIG = {
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


async def init_db_connection():
    await Tortoise.init(CONFIG)
    await Tortoise.generate_schemas()
