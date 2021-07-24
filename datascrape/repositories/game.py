from sqlalchemy import Column, Integer, String, DateTime
from datascrape.repositories.base import Base


class Game(Base):
    __tablename__ = 'games_footywire'
    id = Column(Integer, primary_key=True)
    home_team = Column(String)
    away_team = Column(String)
    venue = Column(String)
    crowd = Column(Integer)
    home_score = Column(Integer)
    away_score = Column(Integer)
    winner = Column(String)
    date_time = Column(DateTime)
    year = Column(Integer)
    round_number = Column(Integer)
    updated_at = Column(DateTime)

    def __repr__(self):
        return "<Game(id='%s', home_team='%s', away_team='%s', \
venue='%s', crowd='%s', home_score='%s', \
away_score='%s', winner='%s', date='%s', year='%s', round='%s', \
updated_at='%s')>" % (self.id, self.home_team, self.away_team, self.venue, self.crowd,
                      self.home_score, self.away_score, self.winner,
                      self.date_time, self.year,
                      self.round_number, self.updated_at)
