import logging.config

from datascrape.logging_config import LOGGING_CONFIG

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


class DataReader:

    def read(self, session=None, team=None):
        LOGGER.error("Should not be calling read on base DataReader")