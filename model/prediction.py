from sqlalchemy import Column, Integer, Sequence, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from model.api_model.user import User
from model.ml_model import MLModel
from model.base import Base


class Prediction(Base):
    __tablename__ = 'prediction'
    id = Column(Integer, Sequence('prediction_id_seq'), primary_key=True)
    model_id = Column(Integer, ForeignKey(MLModel.id))
    user_id = Column(Integer, ForeignKey(User.id))
    team = Column(String)
    team_score = Column(Float)
    opponent = Column(String)
    opponent_score = Column(Float)
    winner = Column(String)
    created_at = Column(DateTime, nullable=False)
    new_model = Column(Boolean, nullable=False)
    prediction_for_user = relationship(User, back_populates='prediction_for_user')
    prediction_for_model = relationship(MLModel, back_populates='prediction_for_model')

    def __repr__(self):
        return "<Prediction(id='%s', model_id='%s', user_id='%s', " \
               "team='%s', team_score='%s', opponent='%s', " \
               "opponent_score='%s', winner='%s', " \
               "created_at='%s', new_model='%s')>" % (self.id, self.model_id, self.user_id, self.team,
                                                      self.team_score,
                                                      self.opponent,
                                                      self.opponent_score, self.winner, self.created_at, self.new_model)
