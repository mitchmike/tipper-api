from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from model import Player


class PlayerSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Player
        load_instance = True
