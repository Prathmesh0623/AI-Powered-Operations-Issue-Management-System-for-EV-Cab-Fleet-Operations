import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration, loaded from environment variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///ai_ops.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_ACCESS_TOKEN_EXPIRES = 60 * 60 * 8  # 8 hours

    JSON_SORT_KEYS = False
    DEBUG = False


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    """
    Used when FLASK_ENV=production. Fails fast if a real secret hasn't been
    set — better to crash on startup than to silently run with dev-secret-key.
    """
    DEBUG = False

    def __init__(self):
        if self.SECRET_KEY == "dev-secret-key" or self.JWT_SECRET_KEY == "dev-jwt-secret-key":
            raise RuntimeError(
                "SECRET_KEY / JWT_SECRET_KEY must be set to real values via environment "
                "variables before running in production (FLASK_ENV=production)."
            )
        if self.SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
            raise RuntimeError(
                "SQLite is for local development only. Set DATABASE_URL to a PostgreSQL "
                "connection string before running in production."
            )


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    return {"production": ProductionConfig, "testing": TestingConfig}.get(env, DevelopmentConfig)
