import click
from flask import current_app, g
from flask.cli import with_appcontext
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from model.base import Base


def init_app(app):
    app.teardown_appcontext(teardown_db)
    app.cli.add_command(init_db_command)
    init_db()


def init_db():
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    Base.metadata.create_all(engine)


def get_db():
    if 'engine' not in g:
        g.engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    return g.engine


def get_db_session_factory():
    if 'session_maker' not in g:
        engine = get_db()
        g.session_maker = sessionmaker(bind=engine)
    return g.session_maker


def new_session():
    if 'session' not in g:
        session_maker = get_db_session_factory()
        g.session = session_maker()
    return g.session


def teardown_db(e=None):
    session = g.pop('session', None)
    engine = g.pop('engine', None)
    if session is not None:
        session.close()
    if engine is not None:
        engine.dispose()


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Create new tables if not existing"""
    init_db()
    click.echo('Initialized the database.')
