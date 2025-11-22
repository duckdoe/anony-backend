import os
import bcrypt
import psycopg as pg
from dotenv import load_dotenv
from flask import jsonify

load_dotenv()

DB_NAME = os.getenv("DBNAME")
DB_USER = os.getenv("DBUSER")
DB_PASSWORD = os.getenv("DBPASSWORD")
DB_HOST = os.getenv("DBHOST")
DB_PORT = os.getenv("DBPORT")


salt = bcrypt.gensalt()


def conn():
    return pg.connect(os.getenv("DATABASE_URL"))


def create_table():
    with conn() as c:
        cur = c.cursor()
        cur.execute(
            """CREATE TABLE IF NOT EXISTS users(
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        username varchar(50) UNIQUE NOT NULL,
                        password TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages(
                    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                    user_id UUID REFERENCES users(id) NOT NULL,
                    message TEXT NOT NULL
                );
                """
        )
        c.commit()


create_table()


def get_user(all=False, **kwargs):
    keys = "=%s AND ".join(kwargs.keys()) + "=%s "
    values = tuple(v for v in kwargs.values())

    with conn() as c:
        cur = c.cursor()
        cur.execute(f"""SELECT * FROM users WHERE {keys}""", values)

        data = cur.fetchone() if all is False else cur.fetchall

    if type(data) == tuple:
        id, username, password = data
        return {"id": id, "username": username, "password": password}

    if type(data) == list:
        user_list = []
        for d in data:
            id, username, password = d
            user_list.append(
                {
                    "id": id,
                    "username": username,
                    "password": password,
                }
            )
        return user_list


def get_messages(all=False, **kwargs):
    keys = "=%s AND ".join(kwargs.keys()) + "=%s"
    values = tuple(v for v in kwargs.values())

    with conn() as c:
        cur = c.cursor()
        cur.execute(f"""SELECT * FROM messages WHERE {keys}""", values)
        data = cur.fetchone() if all is False else cur.fetchall()

    if type(data) == tuple:
        id, user_id, message, created_at = data
        return {
            "id": id,
            "user_id": user_id,
            "message": message,
            "created_at": created_at,
        }

    if type(data) == list:
        message_list = []
        for d in data:
            id, user_id, message, created_at = d
            message_list.append(
                {
                    "id": id,
                    "user_id": user_id,
                    "message": message,
                    "created_at": created_at,
                }
            )
        return message_list


def add_message(user_id, message):

    with conn() as c:
        cur = c.cursor()
        cur.execute(
            """INSERT INTO messages (user_id, message) VALUES(%s, %s)""",
            (user_id, message),
        )
        c.commit()
    return {"message": "user signup successful"}, 200


def add_user(username, password):
    hashed_password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
    try:
        with conn() as c:
            cur = c.cursor()
            cur.execute(
                """INSERT INTO users(username, password) VALUES (%s, %s)""",
                (username, hashed_password),
            )
            c.commit()
        return jsonify({"message": "user created successfully"}), 201
    except pg.errors.UniqueViolation:
        return jsonify({"error": "user with username already exists"}), 409
