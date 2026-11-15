from flask import Flask, jsonify, request

from app.config import (
    API_PASSWORD,
    API_SECRET_KEY,
    API_USERNAME,
    DATABASE,
    DEBUG,
    CORS_ALLOWED_ORIGINS,
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
    app.config["CORS_ALLOWED_ORIGINS"] = CORS_ALLOWED_ORIGINS

    init_db(app.config["DATABASE"])

    from app.auth import auth_bp
    from app.reservas import reservas_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(reservas_bp)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin in app.config["CORS_ALLOWED_ORIGINS"]:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add("Vary", "Origin")
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Max-Age"] = "600"
        return response

    @app.get("/")
    def inicio():
        return jsonify({"service": "api-reservas-hotel", "status": "ok"})

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app
