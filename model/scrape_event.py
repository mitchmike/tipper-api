from sqlalchemy import Column, Integer, String, DateTime, Boolean, Sequence

from model.base import Base


class ScrapeEvent(Base):
    __tablename__ = 'scrape_event'
    id = Column(Integer, Sequence('scrape_id_seq'), primary_key=True)
    type = Column(String)
    status = Column(Boolean, default=False)
    rows_updated = Column(Integer)
    start_time = Column(DateTime)
    end_time = Column(DateTime)

    def __init__(self, type, status, rows_updated, start_time, end_time):
        self.type = type
        self.status = status
        self.rows_updated = rows_updated
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return "<Scrape(id='%s', type='%s', status='%s', \
rows_updated='%s',start_time='%s', end_time='%s')>" % (self.id, self.type, self.status, self.rows_updated,
                                                     self.start_time, self.end_time)

