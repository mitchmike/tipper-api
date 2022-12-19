import datetime

from sqlalchemy import Column, Integer, String, DateTime, Sequence, ARRAY, ForeignKey
from sqlalchemy.orm import relationship

from model.base import Base
from model.team import Team


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, Sequence('user_id_seq'), primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    roles = Column(ARRAY(String), default=ARRAY(String))
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    follows_team = Column(Integer, ForeignKey(Team.id))
    user_follows_team = relationship('Team', back_populates='followers')
    prediction_for_user = relationship('Prediction', back_populates='prediction_for_user')

    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.roles = []
        self.created_at = datetime.datetime.now()
        self.updated_at = datetime.datetime.now()

    def __repr__(self):
        return "<User(id='%s', first_name='%s', last_name='%s', " \
                "email='%s', roles='%s', " \
               "created_at='%s', updated_at='%s')>" % (self.id, self.first_name,
                                                       self.last_name, self.email, self.roles,
                                                       self.created_at, self.updated_at)

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'password'}
