from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model import MatchStatsPlayer


class MatchStatsSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MatchStatsPlayer
        include_relationships = True
        load_instance = True
