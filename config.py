import os


class Config:
    ENV_NAME = 'NONE'
    SECRET_KEY = os.getenv("SECRET_KEY", "this-is-the-default-key")
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',)
    MODEL_FILE_PATH = os.getenv('MODEL_FILE_PATH',)
    CACHE_TYPE = "SimpleCache"
    CACHE_DEFAULT_TIMEOUT = 300


class ProductionConfig(Config):
    ENV_NAME = 'PROD'


class StagingConfig(Config):
    ENV_NAME = 'STAGING'


class DevelopmentConfig(Config):
    ENV_NAME = 'DEV'
