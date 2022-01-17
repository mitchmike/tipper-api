from marshmallow_sqlalchemy import SQLAlchemyAutoSchema, auto_field
from api.model.game import Game


class GameSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Game
        include_relationships = True
        load_instance = True
