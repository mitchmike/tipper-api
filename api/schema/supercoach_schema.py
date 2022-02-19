from marshmallow import fields
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model import PlayerSupercoach


class SuperCoachSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = PlayerSupercoach
        include_relationships = True
        load_instance = True
        exclude = ('round_salary',)
        include = {'player.team': fields.Str(), 'player.name_key': fields.Str()}
