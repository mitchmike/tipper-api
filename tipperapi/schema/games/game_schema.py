from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model.game import Game


class GameSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Game
        include_relationships = False
        load_instance = True
