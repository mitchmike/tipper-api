from marshmallow.fields import Nested
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema

from tipperapi.schema.ml_model_schema import MLModelSchema
from model import Prediction


class PredictionSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Prediction
        include_relationships = True
        load_instance = True
    prediction_for_model = Nested(MLModelSchema)
