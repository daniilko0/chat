from datetime import datetime

from tortoise import Model, fields

from database.types import AttachmentType


class User(Model):
    id = fields.IntField(pk=True)
    username = fields.CharField(max_length=30, unique=True)
    password = fields.CharField(max_length=30)


class Attachment(Model):
    id = fields.UUIDField(pk=True)
    type = fields.CharEnumField(AttachmentType, max_length=5)
    path = fields.CharField(max_length=50)


class Room(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=30)

    def get_all_rooms(self):
        return self.all()

    def __str__(self):
        return self.name


class Message(Model):
    id = fields.IntField(pk=True)
    room = fields.ForeignKeyField("models.Room", related_name="room")
    user = fields.ForeignKeyField("models.User", related_name="user", null=True)
    text = fields.TextField(null=True)
    attachment = fields.ForeignKeyField(
        "models.Attachment",
        related_name="attachment",
        null=True,
    )
    created_at = fields.DatetimeField(default=datetime.now)

    def __str__(self):
        return self.text

    def as_dict(self):
        return {
            "text": self.text,
            "created_at": self.created_at,
            "user": self.user,
            "attachment": self.attachment,
            "room": self.room,
        }
