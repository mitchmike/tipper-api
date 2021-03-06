from sqlalchemy import Column, Integer, Float, DateTime, Sequence, ForeignKey
from sqlalchemy.dialects.postgresql import MONEY
from sqlalchemy.orm import relationship

from model.base import Base


class PlayerFantasy(Base):
    __tablename__ = 'player_fantasy'
    id = Column(Integer, Sequence('fantasy_id_seq'), primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    year = Column(Integer)
    round = Column(Integer)
    round_ranking = Column(Integer)
    round_salary = Column(MONEY)
    round_score = Column(Integer)
    round_value = Column(Float)
    updated_at = Column(DateTime)
    player = relationship("Player", back_populates="fantasy_points")

    def __repr__(self):
        return "<PlayerFantasy(id='%s', player_id='%s', year='%s', round='%s', \
round_ranking='%s',round_salary='%s',round_score='%s',round_value='%s', updated_at='%s')>" % (self.id, self.player_id,
                                                                                              self.year,
                                                                                              self.round,
                                                                                              self.round_ranking,
                                                                                              self.round_salary,
                                                                                              self.round_score,
                                                                                              self.round_value,
                                                                                              self.updated_at)
