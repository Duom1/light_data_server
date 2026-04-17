from flask import request, Flask, g, jsonify
import json
import sqlite3
from dotenv import load_dotenv
import os


load_dotenv()


DATABASE = "data.db"
API_TOKEN = os.getenv("API_TOKEN")


app = Flask(__name__)


def require_token():
    token = request.headers.get("X-API-Token")
    if token != API_TOKEN:
        return False
    return True


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row  # optional but recommended
    return g.db


def init_db():
    db = sqlite3.connect(DATABASE)
    with open("schema.sql") as f:
        db.executescript(f.read())
    db.close()


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route('/addData', methods=['POST'])
def addData():
    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    time = data["time"];
    light = data["light"];
    angle = data["angle"];

    if type(light) != int or type(angle) != int or type(time) != int:
        return "data needs to be integers", 422

    e = f"""
    INSERT INTO data_table (timestamp, light, angle)
    VALUES ({time}, {light}, {angle});
    """

    con = get_db()
    cur = con.cursor()

    cur.executescript(e)
    con.commit()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run()

