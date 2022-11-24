from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow_sqlalchemy.fields import Nested

from api.schema.match_stats_schema import MatchStatsSchema
from model.game import Game


class GameMatchStatsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Game
        include_relationships = True
        load_instance = True
    match_stats_player = Nested(MatchStatsSchema, many=True)
