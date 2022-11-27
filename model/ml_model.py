from datetime import datetime

from sqlalchemy import Integer, Sequence, Column, String, Float, Boolean, DateTime

from model.base import Base


class MLModel(Base):
    __tablename__ = 'ml_model'
    id = Column(Integer, Sequence('ml_model_id_seq'), primary_key=True)
    model_type = Column(String)
    accuracy = Column(Float)
    active = Column(Boolean)
    file_name = Column(String)
    updated_time = Column(DateTime)

    def __init__(self, model_type, accuracy, active, file_name):
        self.model_type = model_type
        self.accuracy = accuracy
        self.active = active
        self.file_name = file_name
        self.updated_time = datetime.now()

    def __repr__(self):
        return "<MLModel(id='%s', model_type='%s', accuracy='%s', active='%s', file_name='%s', updated_time='%s')>" % (
            self.id, self.model_type, self.accuracy, self.active, self.file_name, self.updated_time)
