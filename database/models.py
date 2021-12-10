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
