from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model import PlayerFantasy


class FantasySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PlayerFantasy
        include_relationships = True
        load_instance = True
        exclude = ('round_salary',)
        include = {'player.team': fields.Str(), 'player.name_key': fields.Str()}
