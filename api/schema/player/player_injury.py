from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested

from api.schema.injury_schema import InjurySchema
from model import Player


class PlayerInjurySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Player
        include_relationships = True
        load_instance = True
        exclude = ('match_stats_player', 'fantasy_points', 'supercoach_points')
    injuries = Nested(InjurySchema, many=True)
