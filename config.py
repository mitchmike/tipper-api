import os


class Config:
    ENV_NAME = 'NONE'
    SECRET_KEY = os.getenv("SECRET_KEY", "this-is-the-default-key")
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',)


class ProductionConfig(Config):
    ENV_NAME = 'PROD'
    SECRET_KEY = 'prod-key'


class StagingConfig(Config):
    ENV_NAME = 'STAGING'
    SECRET_KEY = 'staging-key'


class DevelopmentConfig(Config):
    ENV_NAME = 'DEV'
    SECRET_KEY = 'dev-key'
