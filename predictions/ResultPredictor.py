import joblib
import pandas as pd
from flask import json

from api.route.select_api import get_pcnt_diff
from model import MLModel


class ResultPredictor:

    def __init__(self, session, team, opponent, model_type, model_strategy, fields, weightings, round_numbers):
        self.session = session
        self.team = team
        self.opponent = opponent
        self.model_type = model_type
        self.model_strategy = model_strategy
        self.fields = fields
        self.weightings = []  # TODO
        self.round_numbers = []  # TODO

    def get_prediction(self):
        # TODO check cache for matching prediction

        # build pcnt diff dataset for prediction
        # TODO consider player lists, rounds used, weightings
        team_data = get_pcnt_diff(self.session, self.team, 2022)
        opp_data = get_pcnt_diff(self.session, self.opponent, 2022)
        df_team = pd.read_json(json.dumps(team_data))
        df_opp = pd.read_json(json.dumps(opp_data))
        X_team = df_team[self.fields]
        X_opp = df_opp[self.fields]

        # check DB for matching model and run predict with that
        model_record = self.session.query(MLModel)\
            .filter(MLModel.model_type == self.model_type,
                    MLModel.fields == self.fields,
                    MLModel.active == True).first()
        file = None
        if model_record is not None:
            file = model_record.file_name

        # TODO as last resort, build a new model (warn user of time required?)

        # predict
        # TODO cleanup
        if file is not None:
            model = joblib.load('G:\\Code\\Tiplos\\tipper-api\\predictions\\' + file)  # TODO - file path fixup
            t = model.predict(X_team.append(X_team.agg(['mean'])).loc[['mean']])[0]
            o = model.predict(X_opp.append(X_opp.agg(['mean'])).loc[['mean']])[0]
            prediction = {self.team: t, self.opponent: o, 'winner': self.team if t > o else self.opponent}
            return prediction

