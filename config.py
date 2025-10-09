import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "MYSQL_URL",
        # fallback local (ej. Docker MySQL):
        "mysql+pymysql://user:password@127.0.0.1:3306/ia_t2_filtrospam?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SPAM_THRESHOLD = float(os.environ.get("SPAM_THRESHOLD", "0.5"))

class Prod(Config):
    pass

class Dev(Config):
    DEBUG = True
