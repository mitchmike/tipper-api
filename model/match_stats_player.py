from sqlalchemy import Column, Integer, Float, String, DateTime, Sequence, ForeignKey
from sqlalchemy.orm import relationship
from model.base import Base


class MatchStatsPlayer(Base):
    __tablename__ = 'matchstats_player'
    id = Column(Integer, Sequence('match_stat_id_seq'), primary_key=True)
    game_id = Column(Integer, ForeignKey('games_footywire.id'))
    player_id = Column(Integer, ForeignKey('players.id'))
    player_name = Column(String)
    team = Column(String)
    kicks = Column(Integer)
    handballs = Column(Integer)
    disposals = Column(Integer)
    marks = Column(Integer)
    goals = Column(Integer)
    behinds = Column(Integer)
    tackles = Column(Integer)
    hit_outs = Column(Integer)
    goal_assists = Column(Integer)
    inside_50s = Column(Integer)
    clearances = Column(Integer)
    clangers = Column(Integer)
    rebound_50s = Column(Integer)
    frees_for = Column(Integer)
    frees_against = Column(Integer)
    contested_possessions = Column(Integer)
    uncontested_possessions = Column(Integer)
    effective_disposals = Column(Integer)
    disposal_efficiency = Column(Float)
    contested_marks = Column(Integer)
    marks_inside_50 = Column(Integer)
    one_percenters = Column(Integer)
    bounces = Column(Integer)
    centre_clearances = Column(Integer)
    stoppage_clearances = Column(Integer)
    score_involvements = Column(Integer)
    metres_gained = Column(Integer)
    turnovers = Column(Integer)
    intercepts = Column(Integer)
    tackles_inside_50 = Column(Integer)
    time_on_ground_pcnt = Column(Integer)
    updated_at = Column(DateTime)
    player = relationship("Player", back_populates="match_stats_player")
    game = relationship("Game", back_populates="match_stats_player")

    @staticmethod
    def summable_cols():
        return ['kicks',
                'handballs',
                'disposals',
                'marks',
                'goals',
                'behinds',
                'tackles',
                'hit_outs',
                'goal_assists',
                'inside_50s',
                'clearances',
                'clangers',
                'rebound_50s',
                'frees_for',
                'frees_against',
                'contested_possessions',
                'uncontested_possessions',
                'effective_disposals',
                'contested_marks',
                'marks_inside_50',
                'one_percenters',
                'bounces',
                'centre_clearances',
                'stoppage_clearances',
                'score_involvements',
                'metres_gained',
                'turnovers',
                'intercepts',
                'tackles_inside_50'
                ]

    def __repr__(self):
        return "<MatchStatsPlayer(id='%s', player_id='%s', game_id='%s', team='%s', player_name='%s', kicks='%s', " \
               "handballs='%s', " \
               "disposals='%s', marks='%s', goals='%s', behinds='%s', tackles='%s', hit_outs='%s', goal_assists='%s', " \
               "inside_50s='%s', clearances='%s', clangers='%s', rebound_50s='%s', frees_for='%s', " \
               "frees_against='%s', contested_possessions='%s', uncontested_possessions='%s', " \
               "effective_disposals='%s', disposal_efficiency='%s', contested_marks='%s', marks_inside_50='%s', " \
               "one_percenters='%s', bounces='%s', centre_clearances='%s', stoppage_clearances='%s', " \
               "score_involvements='%s', " \
               "metres_gained='%s', turnovers='%s', intercepts='%s', tackles_inside_50='%s', " \
               "time_on_ground_pcnt='%s', updated_at='%s')>" % (
                   self.id, self.player_id, self.game_id, self.team, self.player_name,
                   self.kicks, self.handballs, self.disposals, self.marks,
                   self.goals, self.behinds, self.tackles, self.hit_outs,
                   self.goal_assists, self.inside_50s, self.clearances,
                   self.clangers, self.rebound_50s, self.frees_for,
                   self.frees_against, self.contested_possessions,
                   self.uncontested_possessions, self.effective_disposals,
                   self.disposal_efficiency, self.contested_marks,
                   self.marks_inside_50, self.one_percenters, self.bounces,
                   self.centre_clearances, self.stoppage_clearances,
                   self.score_involvements, self.metres_gained,
                   self.turnovers, self.intercepts, self.tackles_inside_50,
                   self.time_on_ground_pcnt, self.updated_at)
