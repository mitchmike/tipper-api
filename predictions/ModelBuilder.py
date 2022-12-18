import time
import traceback
from datetime import datetime
from os import getenv
import logging.config

import joblib
from dotenv import load_dotenv
from flask import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression

from datascrape.logging_config import LOGGING_CONFIG
from model import Team, MLModel, MatchStatsPlayer
from model.base import Base
from api.route.select_api import get_pcnt_diff

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


class ModelBuilder:

    # TODO different strategies for diff modeltypes etc.
    def __init__(self, session, modelType, fields, target_variable):
        self.session = session
        self.modelType = modelType
        self.features = fields
        self.target_variable = target_variable

    def build(self):
        LOGGER.info("Starting model build")
        data = []
        try:
            teams = self.session.query(Team).all()
            for team in teams:
                for game in get_pcnt_diff(self.session, team.team_identifier, [2021, 2022]):
                    data.append(game)
            df = pd.read_json(json.dumps(data))
            X = df[self.features]
            y = df[self.target_variable]
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
            lm = LinearRegression()
            lm.fit(X_train, y_train)
            model_record = MLModel()
            model_record.model_type = self.modelType
            model_record.model_strategy = "pcnt_diff"
            model_record.features = sorted(self.features)
            model_record.target_variable = self.target_variable
            model_record.active = True  # TODO replace previously active model when creating new one
            model_record.created_at = datetime.now()
            self.analyse(lm, X_test, y_test, model_record)
            self.save_to_file(lm, model_record)
            self.save_to_db(model_record)
            return lm
        except Exception as e:
            LOGGER.error(e)
            LOGGER.error(traceback.format_exc())
        finally:
            self.session.close()

    def save_to_db(self, model_record):
        self.session.add(model_record)
        self.session.commit()

    def save_to_file(self, model, model_record):
        ts = time.time_ns()
        # TODO fix up file path
        file_name = 'G:\\Code\\Tiplos\\tipper-api\\predictions\\model_files\\' + self.modelType + "_" + str(ts) + ".sav"
        LOGGER.info(f'saving to file {file_name}')
        joblib.dump(model, file_name)
        model_record.file_name = file_name

    # TODO different metrics for each type of model
    def analyse(self, model, X_t, y_t, model_record):
        predicted = np.int64(np.round(model.predict(X_t)))
        actual = np.array(y_t)
        if self.target_variable == 'win':
            tpcount_WinPredicted = 0
            fncount_WinNotPredicted = 0
            tncount_LossPredicted = 0
            fpcount_LossNotPredicted = 0
            for i in range(len(predicted)):
                # Wins
                if actual[i] == 1:
                    if predicted[i] == 1:
                        tpcount_WinPredicted += 1
                    else:
                        fncount_WinNotPredicted += 1
                # Losses
                elif actual[i] == 0:
                    if predicted[i] == 0:
                        tncount_LossPredicted += 1
                    else:
                        fpcount_LossNotPredicted += 1
            accuracy = (tpcount_WinPredicted + tncount_LossPredicted) / len(predicted)
            # positiveprediction value
            precision = tpcount_WinPredicted / (tpcount_WinPredicted + fpcount_LossNotPredicted)
            # true positive rate
            recall = tpcount_WinPredicted / (tpcount_WinPredicted + fncount_WinNotPredicted)
            results = {
                'accuracy': accuracy,
                'precision': precision,
                'recall': recall,
                'true_positives': tpcount_WinPredicted,
                'false_negatives': fncount_WinNotPredicted,
                'true_negatives': tncount_LossPredicted,
                'false_positives': fpcount_LossNotPredicted
            }
            model_record.results = results
        model_record.score = model.score(X_t, y_t)

    @staticmethod
    def available_features():
        return [x for x in MatchStatsPlayer.summable_cols() if
                x not in ['score_involvements', 'bounces', 'one_percenters', 'clangers', 'goal_assists']]


if __name__ == '__main__':
    start_all = datetime.now()
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    Base.metadata.create_all(db_engine, checkfirst=True)
    Session = sessionmaker(bind=db_engine)
    session = Session()
    all_features = ModelBuilder.available_features()
    ModelBuilder(session, "LinearRegression", list(all_features), 'score').build()
    LOGGER.info(f'Total time taken: {datetime.now() - start_all}')