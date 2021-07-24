from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from datascrape.repositories.base import Base


class Milestone(Base):
    __tablename__ = 'milestones'
    id = Column(Integer, primary_key=True)
    run_id = Column(BigInteger)
    match_id = Column(Integer)
    mode = Column(String)
    milestone = Column(String)
    milestone_time = Column(DateTime)

    def __repr__(self):
        return "<Game(id='%s', matchid='%s', milestone='%s', milestone_time='%s')>" % (
            self.id, self.match_id, self.milestone, self.milestone_time)
