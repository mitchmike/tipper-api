from unittest import TestCase
import os
from dotenv import load_dotenv

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from model import base

load_dotenv()
TEST_DB_CONN_STRING = os.getenv('DATABASE_URL_TEST')

class BaseScraperTest(TestCase):

    @classmethod
    def setUpClass(cls):
        BaseScraperTest._engine = create_engine(TEST_DB_CONN_STRING)
        base.Base.metadata.create_all(BaseScraperTest._engine, checkfirst=True)
        BaseScraperTest.Session = sessionmaker(bind=BaseScraperTest._engine)
