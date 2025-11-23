import os
import bcrypt
import jwt
import secrets
from flask import request
from flask import make_response
from flask import jsonify
from flask import url_for
from dotenv import load_dotenv
from app import app
from .models import add_user
from .models import add_message
from .models import get_user
from .models import get_messages

load_dotenv()


app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")


@app.get("/")
def index():
    bearer_token = request.headers.get("Authorization")
    if not bearer_token or bearer_token.startswith("Bearer") == False:
        return (
            jsonify(
                {
                    "error": "No bearer token found",
                    "redirect": url_for("login"),
                }
            ),
            403,
        )

    token = bearer_token.split()[1]
    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])
    except (
        jwt.InvalidTokenError,
        jwt.InvalidSignatureError,
        jwt.ExpiredSignatureError,
    ):
        return jsonify({"error": "Invalid or expired jwt token"}), 409

    name = payload["username"]
    user = get_user(name)
    if not user:
        return {"error": "user not found"}, 404

    return {
        "message": "user found",
        "redirect": url_for(messages, username=name),
    }


@app.post("/signup")
def signup():
    if request.is_json:
        data = request.get_json()

        username = data.get("username").lower()
        password = data.get("password")

        return add_user(username, password)

    return jsonify({"error": "only json data can be recieved"}), 400


@app.post("/login")
def login():
    if request.is_json:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not all([username, password]):
            return jsonify({"error": "Missing fields in payload"}), 400

        user = get_user(username=username)
        if not user:
            return {"error": "user not found"}, 404

        stored_pw = user.get("password")
        is_same_pw = bcrypt.checkpw(password.encode("utf-8"), stored_pw.encode("utf-8"))
        if not is_same_pw:
            return jsonify({"error": "Invalid password"}), 400

        token = jwt.encode(
            {"username": username, "user_id": str(user.get("id"))},
            os.getenv("SECRET_KEY"),
            algorithm="HS256",
        )
        return jsonify(
            {
                "message": "login successful",
                "token": token,
                "redirect": url_for("messages", username=username),
            }
        )

    return jsonify({"error": "only json data can be recieved"}), 400


@app.get("/messages")
def messages():
    username = request.args.get("username")
    if not username:
        return jsonify({"error": "search parameter username was not found"}), 404

    user = get_user(username=username)
    if not user:
        return jsonify({"error": "user not found"}), 404

    bearer_token = request.headers.get("Authorization")
    if not bearer_token:
        return jsonify({"error": "No bearer token provided"})

    if not bearer_token.startswith("Bearer"):
        return {
            "error": "Bad request no bearer token found",
            "redirect": url_for("login"),
        }, 400

    token = bearer_token.split()[1]
    if not username:
        return {"error": "Missing field in payload"}, 400

    if not token:
        return {"error": "no token provided"}

    try:
        payload = jwt.decode(token, os.getenv("SECRET_KEY"), algorithms=["HS256"])

        if payload["username"] != username:
            return jsonify({"message": "Invalid token"}), 400

    except (
        jwt.InvalidTokenError,
        jwt.InvalidSignatureError,
        jwt.ExpiredSignatureError,
    ):
        return jsonify({"message": "Invalid or expired token"}), 400

    user_messages = get_messages(
        all=True,
        user_id=user.get("id"),
    )
    if not user_messages:
        return jsonify({"error": "No messages found for this user"}), 404
    return (
        jsonify(
            {
                "user_id": user.get("id"),
                "messages": user_messages,
            }
        ),
        200,
    )


@app.post("/send-message")
def send_message():
    user_id = request.args.get("id")
    if not user_id:
        return jsonify({"error": "Missing field in url"}), 400

    user = get_user(id=user_id)
    if not user:
        return {"error": "user not found"}, 404

    if request.is_json:
        data = request.get_json()
        message = data.get("message")

        if not message:
            return jsonify({"error": "Empty message body"}), 400

        if len(message) < 10:
            return (
                jsonify(
                    {"error": "A minimum of ten characters is needed to send a message"}
                ),
                400,
            )

        add_message(user_id, message)
        return jsonify({"message": "message sent successfully"}), 201

    return jsonify({"error": "only json data can be recieved"}), 400
