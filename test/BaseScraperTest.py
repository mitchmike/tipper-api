from unittest import TestCase

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datascrape.repositories import base

TEST_DB_CONN_STRING = 'postgresql://postgres:oscar12!@localhost:5432/tiplos-test?gssencmode=disable'


class BaseScraperTest(TestCase):

    @classmethod
    def setUpClass(cls):
        BaseScraperTest._engine = create_engine(TEST_DB_CONN_STRING)
        base.Base.metadata.create_all(BaseScraperTest._engine, checkfirst=True)
        BaseScraperTest.Session = sessionmaker(bind=BaseScraperTest._engine)
