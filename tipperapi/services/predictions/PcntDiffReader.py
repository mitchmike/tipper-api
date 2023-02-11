from tipperapi.services.predictions.DataReader import DataReader
from tipperapi.services.predictions.aggregated_match_stats import get_pcnt_diff, ALL_ROUNDS


class PcntDiffReader(DataReader):

    def read(self, session=None, team_identifier=None):
        return get_pcnt_diff(session, team_identifier, [(2021, ALL_ROUNDS), (2022, ALL_ROUNDS)])
