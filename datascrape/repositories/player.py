from sqlalchemy import Column, Integer, String, Date, DateTime, Sequence, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from datascrape.repositories.base import Base


class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, Sequence('player_id_seq'), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    name_key = Column(String, CheckConstraint("name_key <> ''", name='name_key_not_empty'), nullable=False)
    number = Column(Integer)
    team = Column(String)
    games = Column(Integer)
    age = Column(String)
    DOB = Column(Date, nullable=False)
    height = Column(Integer)
    weight = Column(Integer)
    position = Column(String)
    updated_at = Column(DateTime)
    injuries = relationship("Injury", back_populates="player")
    fantasy_points = relationship("PlayerFantasy", back_populates="player")
    supercoach_points = relationship("PlayerSupercoach", back_populates="player")
    __table_args__ = (UniqueConstraint('name_key', 'DOB', 'team', name='uix_1'),)

    def __repr__(self):
        return "<Player(id='%s', number='%s', team='%s', \
first_name='%s', last_name='%s', name_key='%s', games='%s', \
age='%s', DOB='%s', height='%s', weight='%s', \
position='%s', updated_at='%s')>" % (self.id, self.number, self.team, self.first_name,
                                     self.last_name, self.name_key, self.games, self.age, self.DOB, self.height,
                                     self.weight, self.position, self.updated_at)
