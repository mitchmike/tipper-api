from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from model.base import Base


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
    match_stats_player = relationship("MatchStatsPlayer", back_populates="game")

    def __init__(self, game_id=None, home_team=None, away_team=None, year=None, round_number=None):
        self.id = game_id
        self.home_team = home_team
        self.away_team = away_team
        self.year = year
        self.round_number = round_number

    def __repr__(self):
        return "<Game(id='%s', home_team='%s', away_team='%s', \
venue='%s', crowd='%s', home_score='%s', \
away_score='%s', winner='%s', date='%s', year='%s', round='%s', \
updated_at='%s')>" % (self.id, self.home_team, self.away_team, self.venue, self.crowd,
                      self.home_score, self.away_score, self.winner,
                      self.date_time, self.year,
                      self.round_number, self.updated_at)
