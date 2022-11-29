from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model.team import Team


class TeamSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Team
        include_relationships = True
        load_instance = True
