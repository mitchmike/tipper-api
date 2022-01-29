from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine


class MileStoneRecorder:

    def __init__(self, db_connection_string):
        engine = create_engine(db_connection_string)
        session = sessionmaker(bind=engine)
        self.milestone_session = session()

    def add_milestone(self, milestone):
        self.milestone_session.add(milestone)

    def commit_milestones(self):
        self.milestone_session.commit()
        self.milestone_session.close()
