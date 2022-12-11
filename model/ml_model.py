import datetime

from sqlalchemy import Column, Integer, String, DateTime, Sequence, ARRAY, Float, Boolean

from model.base import Base


class MLModel(Base):
    __tablename__ = 'ml_model'
    id = Column(Integer, Sequence('ml_model_id_seq'), primary_key=True)
    model_type = Column(String)
    model_strategy = Column(String)
    fields = Column(ARRAY(String), default=ARRAY(String))
    accuracy = Column(Float)
    precision = Column(Float)
    recall = Column(Float)
    true_positives = Column(Integer)
    false_negatives = Column(Integer)
    true_negatives = Column(Integer)
    false_positives = Column(Integer)
    score = Column(Float)
    file_name = Column(String, unique=True)
    created_at = Column(DateTime, nullable=False)
    active = Column(Boolean, nullable=False)

# TODO add this init back
    # def __init__(self, model_type, model_strategy, fields,
    #              accuracy, precision, recall, true_positives,
    #              false_negatives, true_negatives, false_positives,
    #              score, file_name, active):
    #     self.model_type = model_type
    #     self.model_strategy = model_strategy
    #     self.fields = fields
    #     self.accuracy = accuracy
    #     self.precision = precision
    #     self.recall = recall
    #     self.true_positives = true_positives
    #     self.false_negatives = false_negatives
    #     self.true_negatives = true_negatives
    #     self.false_positives = false_positives
    #     self.score = score
    #     self.file_name = file_name
    #     self.active = active
    #     self.created_at = datetime.datetime.now()

    def __repr__(self):
        return "<MLModel(id='%s', model_type='%s', model_strategy='%s', " \
                "fields='%s', accuracy='%s', " \
                "precision='%s', recall='%s', " \
                "true_positives='%s', false_negatives='%s', " \
                "true_negatives='%s', false_positives='%s', " \
                "score='%s', file_name='%s', " \
               "active='%s', created_at='%s')>" % (self.id, self.model_type, self.model_strategy, self.fields,
                                                   self.accuracy, self.precision, self.recall, self.true_positives,
                                                   self.false_negatives, self.true_negatives, self.false_positives,
                                                   self.score, self.file_name, self.active, self.created_at)
