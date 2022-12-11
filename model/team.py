from sqlalchemy import Column, Integer, String, Boolean, Sequence
from sqlalchemy.orm import relationship

from model.base import Base


class Team(Base):
    __tablename__ = 'teams'
    id = Column(Integer, Sequence('team_id_seq'), primary_key=True)
    city = Column(String)
    name = Column(String)
    team_identifier = Column(String, unique=True)
    active_in_competition = Column(Boolean, default=False)
    followers = relationship('User', back_populates='user_follows_team')

    def __repr__(self):
        return "<Team(id='%s', city='%s', name='%s', \
team_identifier='%s',active_in_competition='%s')>" % (self.id, self.city, self.name, self.team_identifier,
                                                      self.active_in_competition)
