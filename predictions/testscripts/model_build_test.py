import itertools
import logging
from datetime import datetime
from os import getenv

import pandas as pd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from datascrape.logging_config import LOGGING_CONFIG
from predictions.ModelBuilder import ModelBuilder

from random import random

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


def scores_for_different_feature_counts():
    start_all = datetime.now()
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    Session = sessionmaker(bind=db_engine)
    session = Session()
    all_features = ModelBuilder.available_features()
    # sample of values from an iterator
    results = []
    for n in range(4, len(all_features)):
        scores = []
        combos = list(itertools.combinations(all_features, n))
        count = len(combos)
        samplesize = 100
        step = count / samplesize
        index = 0
        for i in range(samplesize):
            skip = round(random() * step)
            index = index + skip
            features = combos[index]
            score = ModelBuilder(session, "LinearRegression", "pcnt_diff", list(features), 'score').build()
            scores.append(score)
        avg_score = sum(scores) / samplesize
        result = {
            'features': n,
            'avg': avg_score,
            'max': max(scores),
            'min': min(scores)
        }
        results.append(result)
        print(f'features: {n}. avg score: {avg_score}, max_score: {max(scores)}, min_score: {min(scores)}')

    df = pd.DataFrame(results)
    plt.plot(df['features'], df['avg'], label='avg')
    plt.plot(df['features'], df['max'], label='max')
    plt.plot(df['features'], df['min'], label='min')
    plt.legend()
    plt.savefig('feature_size_test.png')
    plt.show()
    LOGGER.info(f'Total time taken: {datetime.now() - start_all}')


if __name__ == '__main__':
    scores_for_different_feature_counts()
