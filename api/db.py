import click
from flask import current_app, g
from flask.cli import with_appcontext
from flask_alchemydumps import AlchemyDumps
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from model.base import Base


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    get_db()


def get_db():
    if 'engine' not in g:
        g.engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
        Base.metadata.create_all(g.engine)
    return g.engine


def get_backups(app, db):
    if 'alchemydumps' not in g:
        g.alchemydumps = AlchemyDumps(app, db)
    return g.alchemydumps


def get_db_session_factory():
    if 'Session' not in g:
        engine = get_db()
        g.Session = sessionmaker(bind=engine)
    return g.Session


def new_session():
    Session = get_db_session_factory()
    return Session()


def close_db(e=None):
    g.pop('Session', None)
    engine = g.pop('engine', None)

    if engine is not None:
        engine.dispose()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create new tables if not existing"""
    get_db()
    click.echo('Initialized the database.')
