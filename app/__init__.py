from flask import Flask, render_template

from app.config import (
    API_PASSWORD,
    API_SECRET_KEY,
    API_USERNAME,
    DATABASE,
    DEBUG,
    TOKEN_HOURS,
)
from app.db import init_db


def create_app():
    app = Flask(__name__)
    app.config["SECRET_KEY"] = API_SECRET_KEY
    app.config["API_USERNAME"] = API_USERNAME
    app.config["API_PASSWORD"] = API_PASSWORD
    app.config["TOKEN_HOURS"] = TOKEN_HOURS
    app.config["DATABASE"] = str(DATABASE)
    app.config["DEBUG"] = DEBUG

    init_db(app.config["DATABASE"])

    from app.auth import auth_bp
    from app.reservas import reservas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reservas_bp)

    @app.get("/")
    def inicio():
        return render_template("index.html")

    return app
