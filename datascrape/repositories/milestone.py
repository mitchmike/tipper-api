from sqlalchemy import Column, Integer, String, DateTime
from datascrape.repositories.base import Base


class Milestone(Base):
    __tablename__ = 'milestones'
    id = Column(Integer, primary_key=True)
    milestone = Column(String)
    milestone_time = Column(DateTime)

    def __repr__(self):
        return "<Game(id='%s', milestone='%s', milestone_time='%s')>" % (
            self.id, self.milestone, self.milestone_time)
