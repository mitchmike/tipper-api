from http import HTTPStatus
from flask import Blueprint
from flasgger import swag_from
from api.model.game import Game
from api.schema.game import GameSchema