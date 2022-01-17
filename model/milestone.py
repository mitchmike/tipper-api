import datetime

from sqlalchemy import Column, Integer, String, DateTime, BigInteger, Sequence
from model.base import Base


class Milestone(Base):
    __tablename__ = 'milestones'
    id = Column(Integer, Sequence('milestone_id_seq'), primary_key=True)
    run_id = Column(BigInteger)
    match_id = Column(Integer)
    mode = Column(String)
    milestone = Column(String)
    milestone_time = Column(DateTime)

    def __init__(self, run_id, match_id, mode, milestone_name):
        self.run_id = run_id
        self.match_id = match_id
        self.mode = mode
        self.milestone = milestone_name
        self.milestone_time = datetime.datetime.now()

    def __repr__(self):
        return "<Milestone(id='%s', runid='%s', matchid='%s', mode='%s', milestone='%s', milestone_time='%s')>" % (
            self.id, self.run_id, self.match_id, self.mode, self.milestone, self.milestone_time)
