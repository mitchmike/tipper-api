import datetime
from abc import abstractmethod

from model.scrape_event import ScrapeEvent
from datascrape.scrapers.util.scrape_util import record_scrape_event


class BaseScraper:

    def __init__(self, engine, eventType):
        self.engine = engine
        self.eventType = eventType

    def scrape(self):
        status = False
        rows_updated = 0
        start = datetime.datetime.now()
        try:
            rows_updated = self.scrape_entities()
            status = True
        except Exception as e:
            print(e)
        scrape_event = ScrapeEvent(self.eventType, status, rows_updated, start, datetime.datetime.now())
        record_scrape_event(self.engine, scrape_event)
        return status

    # strategy for subclass - should return an int representing the count of updated rows
    @abstractmethod
    def scrape_entities(self):
        pass
