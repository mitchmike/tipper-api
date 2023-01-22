from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from model import MLModel


class MLModelSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = MLModel
        include_relationships = False
        load_instance = True
