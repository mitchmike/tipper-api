import os
from flask import Flask, jsonify
from api.model.base import Base
from api.model.game import Game
from api.schema.game import GameSchema
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

app = Flask(__name__)
env_config = os.getenv("APP_SETTINGS", "config.DevelopmentConfig")
app.config.from_object(env_config)
engine = create_engine('postgresql://postgres:oscar12!@localhost:5432/tiplos?gssencmode=disable')
Base.metadata.create_all(engine, checkfirst=True)


@app.route("/")
def index():
    secret_key = app.config.get("SECRET_KEY")
    return f"The configured secret key is {secret_key}."


@app.route("/games")
def select_games():
    session = sessionmaker(bind=engine)
    with session() as session:
        games = session.query(Game).all()
        games_schema = GameSchema(many=True)
        dump_data = games_schema.dump(games)
        return jsonify(dump_data)
