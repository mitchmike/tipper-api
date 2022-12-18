import logging

import joblib
import pandas as pd
from flask import json

from api.route.select_api import get_pcnt_diff
from datascrape.logging_config import LOGGING_CONFIG
from model import MLModel
from predictions.ModelBuilder import ModelBuilder

logging.config.dictConfig(LOGGING_CONFIG)
LOGGER = logging.getLogger(__name__)


class ResultPredictor:

    def __init__(self, session, team, opponent, model_type, model_strategy, features, target_variable, weightings,
                 round_numbers):
        self.session = session
        self.team = team
        self.opponent = opponent
        self.model_type = model_type
        self.model_strategy = model_strategy
        self.features = features
        self.target_variable = target_variable
        self.weightings = []  # TODO
        self.round_numbers = []  # TODO

    def get_prediction(self):
        # TODO check cache for matching prediction

        # build pcnt diff dataset for prediction
        # TODO consider player lists, rounds used, weightings
        team_data = get_pcnt_diff(self.session, self.team, [2022])
        opp_data = get_pcnt_diff(self.session, self.opponent, [2022])
        df_team = pd.read_json(json.dumps(team_data))
        df_opp = pd.read_json(json.dumps(opp_data))
        X_team = df_team[self.features]
        X_opp = df_opp[self.features]

        # check DB for matching model and run predict with that
        model_record = self.session.query(MLModel) \
            .filter(MLModel.model_type == self.model_type,
                    MLModel.features == self.features,  # TODO - order of features should not matter
                    MLModel.target_variable == self.target_variable,
                    MLModel.active == True).first()

        model = None
        new_model = False
        if model_record is not None:
            file = model_record.file_name
            if file is not None:
                try:
                    # TODO cleanup
                    model = joblib.load(file)  # TODO - file path fixup
                except FileNotFoundError as e:
                    LOGGER.error(e.strerror)
        if model is None:
            # TODO as last resort, build a new model (warn user of time required?)
            model = ModelBuilder(self.session, "LinearRegression", self.features, self.target_variable).build()
            new_model = True
        if model is not None:
            t = model.predict(X_team.append(X_team.agg(['mean'])).loc[['mean']])[0]
            o = model.predict(X_opp.append(X_opp.agg(['mean'])).loc[['mean']])[0]
            prediction = {self.team: t, self.opponent: o, 'winner': self.team if t > o else self.opponent,
                          'new_model': new_model}
            return prediction
        else:
            return None
