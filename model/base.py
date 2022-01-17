from sqlalchemy.orm import declarative_base

Base = declarative_base()


def as_dict(self):
    return {c.name: getattr(self, c.name) for c in self.__table__.columns}


Base.as_dict = as_dict
