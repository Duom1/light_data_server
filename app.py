from flask import Flask, request, Response, stream_with_context, g, jsonify
from flask_cors import cross_origin
import sqlite3
from dotenv import load_dotenv
import os
import threading


load_dotenv()


API_TOKEN = os.getenv("API_TOKEN")
DATABASE = os.getenv("DB_LOCATION")


app = Flask(__name__)


latest_row = None
condition = threading.Condition()


def require_token():
    token = request.headers.get("X-API-Token")
    if token != API_TOKEN:
        return False
    return True


def get_db():
    conn = sqlite3.connect(DATABASE, check_same_thread=False, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    conn.row_factory = sqlite3.Row  # optional but recommended
    return conn


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


@cross_origin
@app.route('/getDataSse')
def sse():
    def generate():
        global latest_row
        with condition:
            while True:
                condition.wait()
                if latest_row:
                    yield f"data: {jsonify(latest_row)}\n\n"
    return Response(stream_with_context(generate()), mimetype='text/event-stream')


@cross_origin
@app.route('/getData', methods=['GET'])
def getData():

    e = f"""
    SELECT *
    FROM data_table
    ORDER BY timestamp DESC
    LIMIT 10;
    """

    con = get_db()
    cur = con.cursor()

    cur.execute(e)
    # con.commit()

    data = []
    rows = cur.fetchall()
    for row in rows:
        data.append({
            "time": row[0],
            "light": row[1],
            "angle": row[2]
        })

    con.close()

    return jsonify(data), 200


@app.route('/addData', methods=['POST'])
def addData():
    global latest_row

    if not require_token():
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    time = data["time"];
    light = data["light"];
    angle = data["angle"];

    if type(light) != int or type(angle) != int or type(time) != int:
        return jsonify({"error": "data needs to be integers"}, 422)

    e = f"""
    INSERT INTO data_table (timestamp, light, angle)
    VALUES ({time}, {light}, {angle});
    """

    with condition:
        latest_row = data
        condition.notify_all()

    con = get_db()
    cur = con.cursor()

    cur.executescript(e)
    con.commit()
    con.close()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    init_db()
    app.run()

