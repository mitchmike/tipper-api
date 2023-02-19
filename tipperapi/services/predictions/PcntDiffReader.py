from tipperapi.services.predictions.DataReader import DataReader
from tipperapi.services.predictions.aggregated_match_stats import get_pcnt_diff, ALL_ROUNDS


class PcntDiffReader(DataReader):

    def read(self, session=None, team_identifier=None, year_rounds=None):
        if year_rounds is None:
            year_rounds = [(2021, ALL_ROUNDS), (2022, ALL_ROUNDS)]
        return get_pcnt_diff(session, team_identifier, year_rounds)
