from flask import Flask
from config import Dev, Prod
from db.models import db
from web.auth import bp_auth, init_login
from web.routes import bp as bp_web

def create_app(config_obj=Dev):
    app = Flask(__name__)
    app.config.from_object(config_obj)
    db.init_app(app)
    with app.app_context():
        # En MySQL usa migraciones Alembic; para pruebas rápidas:
        # db.create_all()
        pass
    init_login(app)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_web)
    return app

app = create_app()  # para flask run
