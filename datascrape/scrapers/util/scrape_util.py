import logging.config

from sqlalchemy.orm import sessionmaker

LOGGER = logging.getLogger(__name__)


def record_scrape_event(db_engine, event):
    session = sessionmaker(bind=db_engine)
    with session() as session:
        try:
            session.merge(event)
            session.commit()
        except Exception as e:
            LOGGER.exception(f'Caught exception {e} \n'
                             f'Rolling back {event}')
            session.rollback()
