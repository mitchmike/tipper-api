import time
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
from model import Team, MLModel
from model.base import Base
from api.route.select_api import get_pcnt_diff

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


class ModelBuilder:

    # TODO different strategies for diff modeltypes etc.
    def __init__(self, engine, modelType, fields):
        self.engine = engine
        self.modelType = modelType
        self.fields = fields

    def build(self):
        LOGGER.info("Starting model build")
        Base.metadata.create_all(self.engine, checkfirst=True)
        Session = sessionmaker(bind=self.engine)
        data = []
        session = Session()
        try:
            teams = session.query(Team).all()
            for team in teams:
                for game in get_pcnt_diff(session, team.team_identifier, 2022):
                    data.append(game)
            df = pd.read_json(json.dumps(data))
            X = df[self.fields]
            y = df['win']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3)
            lm = LinearRegression()
            lm.fit(X_train, y_train)
            model_record = MLModel()
            model_record.model_type = self.modelType
            model_record.model_strategy = "pcnt_diff"
            model_record.fields = self.fields
            model_record.active = True  # TODO replace previously active model when creating new one
            model_record.created_at = datetime.now()
            self.analyse(lm, X_test, y_test, model_record)
            self.save_to_file(lm, model_record)
            self.save_to_db(session, model_record)
        except Exception as e:
            LOGGER.error(e)
        finally:
            session.close()

    def save_to_db(self, session, model_record):
        session.add(model_record)
        session.commit()

    def save_to_file(self, model, model_record):
        ts = time.time_ns()
        file_name = "model_files/" + self.modelType + "_" + str(ts) + ".sav"
        LOGGER.info(f'saving to file {file_name}')
        joblib.dump(model, file_name)
        model_record.file_name = file_name

    def analyse(self, model, X_t, y_t, model_record):
        predicted = np.int64(np.round(model.predict(X_t)))
        actual = np.array(y_t)
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
        model_record.accuracy = accuracy
        model_record.precision = precision
        model_record.recall = recall
        model_record.true_positives = tpcount_WinPredicted
        model_record.false_negatives = fncount_WinNotPredicted
        model_record.true_negatives = tncount_LossPredicted
        model_record.false_positives = fpcount_LossNotPredicted
        model_record.score = model.score(X_t, y_t)


if __name__ == '__main__':
    start_all = datetime.now()
    load_dotenv()
    db_engine = create_engine(getenv('DATABASE_URL'))
    ModelBuilder(db_engine, "LinearRegression", ['kicks', 'disposals', 'marks', 'handballs']).build()
    LOGGER.info(f'Total time taken: {datetime.now() - start_all}')
