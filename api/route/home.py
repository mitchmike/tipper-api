from http import HTTPStatus
from flask import Blueprint
from flasgger import swag_from
from model.game import Game
from api.schema.game_schema import GameSchema