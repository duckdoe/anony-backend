from flask import Flask
from flask_cors import CORS


def create_app():
    app = Flask(__name__)

    CORS(
        app,
        supports_credentials=True,
        origins=[
            "http://localhost:5500",
            "http://127.0.0.1:5500",
        ],
    )
    return app


app = create_app()
