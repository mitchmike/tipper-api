import datetime
import logging.config

import joblib
import pandas as pd
from flask import json

from tipperapi.services.cache import cache
from tipperapi.schema.prediction_schema import PredictionSchema
from datascrape.logging_config import LOGGING_CONFIG
from model import MLModel, Prediction
from tipperapi.services.predictions.ModelBuilder import ModelBuilder
from tipperapi.services.predictions.aggregated_match_stats import get_pcnt_diff, ALL_ROUNDS

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)

CACHE_KEY = 'model/{}'


class ResultPredictor:

    def __init__(self, session, user_id, team, opponent, model_type, model_strategy, features, target_variable):
        self.session = session
        self.user_id = user_id
        self.team = team
        self.opponent = opponent
        self.model_type = model_type
        self.model_strategy = model_strategy
        self.features = features
        self.target_variable = target_variable
        self.weightings = []  # TODO

    def get_prediction(self, team_year_rounds, opp_year_rounds):
        default_yrs = [(datetime.datetime.now().year, ALL_ROUNDS)]
        team_year_rounds = team_year_rounds if len(team_year_rounds) > 0 else default_yrs
        opp_year_rounds = opp_year_rounds if len(opp_year_rounds) > 0 else default_yrs

        # build pcnt diff dataset for prediction
        # TODO consider player lists, weightings
        team_data = get_pcnt_diff(self.session, self.team, team_year_rounds)
        opp_data = get_pcnt_diff(self.session, self.opponent, opp_year_rounds)
        df_team = pd.read_json(json.dumps(team_data))
        df_opp = pd.read_json(json.dumps(opp_data))
        X_team = df_team[self.features]
        X_opp = df_opp[self.features]

        new_model = False
        model = None
        model_record = self.find_model_in_db()
        # search cache first
        if model_record is not None:
            model = cache.get(CACHE_KEY.format(model_record.id))
        if model is None:
            # then check for file
            if model_record is not None:
                file = model_record.file_name
                if file is not None:
                    try:
                        model = joblib.load(file)
                    except FileNotFoundError as e:
                        LOGGER.error(e.strerror)
            if model is None:
                # if all else fails, build a new model
                model = ModelBuilder(self.session, "LinearRegression", "pcnt_diff", self.features,
                                     self.target_variable).build()
                model_record = self.find_model_in_db()
                new_model = True
        # hopefully we have a model by this point
        if model is not None:
            # save to cache
            if model_record.id is not None:
                cache.set(CACHE_KEY.format(model_record.id), model)
            # perform prediction
            t = model.predict(X_team.append(X_team.agg(['mean'])).loc[['mean']])[0]
            o = model.predict(X_opp.append(X_opp.agg(['mean'])).loc[['mean']])[0]
            winner = self.team if t > o else self.opponent
            prediction = Prediction()
            prediction.user_id = self.user_id
            prediction.model_id = model_record.id
            prediction.team_score = t
            prediction.opponent_score = o
            prediction.new_model = new_model
            prediction.team = self.team
            prediction.opponent = self.opponent
            prediction.winner = winner
            prediction.created_at = datetime.datetime.now()
            self.session.add(prediction)
            self.session.commit()
            schema = PredictionSchema()
            dump_data = schema.dump(prediction)
            return dump_data
        logging.error(f'Could not build model for {self}')
        return None

    def find_model_in_db(self):
        # check DB for matching model and run predict with that
        model_record = self.session.query(MLModel) \
            .filter(MLModel.model_type == self.model_type,
                    MLModel.model_strategy == self.model_strategy,
                    MLModel.features == sorted(self.features),
                    MLModel.target_variable == self.target_variable,
                    MLModel.active == True).first()
        return model_record
