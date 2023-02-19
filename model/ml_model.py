from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Sequence, ARRAY, Float, Boolean, JSON
from sqlalchemy.orm import relationship

from model.base import Base


class MLModel(Base):
    __tablename__ = 'ml_model'
    id = Column(Integer, Sequence('ml_model_id_seq'), primary_key=True)
    model_type = Column(String)
    model_strategy = Column(String)
    features = Column(ARRAY(String), default=ARRAY(String))
    target_variable = Column(String)
    results = Column(JSON)
    score = Column(Float)
    file_name = Column(String, unique=True)
    created_at = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False)
    prediction_for_model = relationship('Prediction', back_populates='prediction_for_model')

    def __init__(self):
        self.features = []
        self.created_at = datetime.now()
        self.active = True

    def __repr__(self):
        return "<MLModel(id='%s', model_type='%s', model_strategy='%s', " \
               "features='%s', target_variable='%s', results='%s', " \
               "score='%s', file_name='%s', " \
               "active='%s', created_at='%s')>" % (self.id, self.model_type, self.model_strategy, self.features,
                                                   self.target_variable,
                                                   self.results,
                                                   self.score, self.file_name, self.active, self.created_at)
