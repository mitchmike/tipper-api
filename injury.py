from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, Sequence, UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

from base import Base


class Injury(Base):
    __tablename__ = 'injuries'
    id = Column(Integer, Sequence('injury_id_seq'), primary_key=True)
    player_id = Column(Integer, ForeignKey('players.id'))
    injury = Column(String)
    returning = Column(String)
    recovered = Column(Boolean, default=False)
    updated_at = Column(DateTime)
    player = relationship("Player", back_populates="injuries")
    def __repr__(self):
        return "<Injury(id='%s', player_id='%s', injury='%s', \
returning='%s',recovered='%s', updated_at='%s')>" % (self.id, self.player_id, self.injury, self.returning, self.recovered, self.updated_at)

