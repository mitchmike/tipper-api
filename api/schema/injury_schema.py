from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model import Injury


class InjurySchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Injury
        include_relationships = True
        load_instance = True
