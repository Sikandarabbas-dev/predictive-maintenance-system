"""
Predictive Maintenance System — Flask REST API

Endpoints:
  POST /api/machines                     -> register a machine
  GET  /api/machines                      -> list machines
  POST /api/readings                      -> log a sensor reading (optionally mark failed=1)
  GET  /api/readings/<machine_id>         -> reading history for a machine
  POST /api/predict/<machine_id>          -> predict current failure risk for a machine
  GET  /api/alerts                        -> list all generated maintenance alerts
  GET  /api/alerts/high-risk               -> machines currently at high risk

Run:
  pip install -r requirements.txt
  python app.py
"""

from flask import Flask, request, jsonify

from db import get_connection, init_sqlite_schema, is_sqlite, USE_SQLITE_FALLBACK
from ml.maintenance_model import PredictiveMaintenanceModel

app = Flask(__name__)

if USE_SQLITE_FALLBACK:
    init_sqlite_schema()


def query(conn, sql, params=(), fetch=False):
    if is_sqlite(conn):
        sql = sql.replace("%s", "?")
        cur = conn.cursor()
        cur.execute(sql, params)
        if fetch:
            rows = [dict(r) for r in cur.fetchall()]
            return rows
        conn.commit()
        return cur.lastrowid
    else:
        cur = conn.cursor(dictionary=True)
        cur.execute(sql, params)
        if fetch:
            rows = cur.fetchall()
            cur.close()
            return rows
        conn.commit()
        last_id = cur.lastrowid
        cur.close()
        return last_id


@app.route("/api/machines", methods=["POST"])
def create_machine():
    data = request.get_json(force=True)
    name = data.get("machine_name")
    mtype = data.get("machine_type", "")
    installed_at = data.get("installed_at")
    if not name:
        return jsonify({"error": "machine_name is required"}), 400

    conn = get_connection()
    mid = query(
        conn,
        "INSERT INTO machines (machine_name, machine_type, installed_at) VALUES (%s, %s, %s)",
        (name, mtype, installed_at),
    )
    conn.close()
    return jsonify({"machine_id": mid, "machine_name": name, "machine_type": mtype}), 201


@app.route("/api/machines", methods=["GET"])
def list_machines():
    conn = get_connection()
    rows = query(conn, "SELECT * FROM machines", fetch=True)
    conn.close()
    return jsonify(rows)


@app.route("/api/readings", methods=["POST"])
def log_reading():
    data = request.get_json(force=True)
    required = ["machine_id", "reading_date", "runtime_hours", "temperature", "vibration", "pressure"]
    if not all(k in data for k in required):
        return jsonify({"error": f"required fields: {required}"}), 400

    conn = get_connection()
    rid = query(
        conn,
        """INSERT INTO sensor_readings
           (machine_id, reading_date, runtime_hours, temperature, vibration, pressure, failed)
           VALUES (%s, %s, %s, %s, %s, %s, %s)""",
        (
            data["machine_id"],
            data["reading_date"],
            data["runtime_hours"],
            data["temperature"],
            data["vibration"],
            data["pressure"],
            int(data.get("failed", 0)),
        ),
    )
    conn.close()
    return jsonify({"reading_id": rid, **data}), 201


@app.route("/api/readings/<int:machine_id>", methods=["GET"])
def reading_history(machine_id):
    conn = get_connection()
    rows = query(
        conn,
        "SELECT * FROM sensor_readings WHERE machine_id = %s ORDER BY reading_date",
        (machine_id,),
        fetch=True,
    )
    conn.close()
    return jsonify(rows)


@app.route("/api/predict/<int:machine_id>", methods=["POST"])
def predict_risk(machine_id):
    conn = get_connection()

    # train on ALL machines' historical readings (pooled) — a shared health model
    all_readings = query(
        conn,
        "SELECT runtime_hours, temperature, vibration, pressure, failed FROM sensor_readings",
        fetch=True,
    )

    latest = query(
        conn,
        """SELECT * FROM sensor_readings WHERE machine_id = %s
           ORDER BY reading_date DESC LIMIT 1""",
        (machine_id,),
        fetch=True,
    )

    if not latest:
        conn.close()
        return jsonify({"error": "no sensor readings found for this machine"}), 400

    latest = latest[0]
    model = PredictiveMaintenanceModel()
    model.fit(all_readings)

    result = model.predict_risk(
        latest["runtime_hours"], latest["temperature"], latest["vibration"], latest["pressure"]
    )

    query(
        conn,
        "INSERT INTO maintenance_alerts (machine_id, failure_risk, risk_level) VALUES (%s, %s, %s)",
        (machine_id, result["failure_risk"], result["risk_level"]),
    )
    conn.close()

    return jsonify({"machine_id": machine_id, "based_on_reading_date": latest["reading_date"], **result})


@app.route("/api/alerts", methods=["GET"])
def list_alerts():
    conn = get_connection()
    rows = query(
        conn,
        """SELECT a.*, m.machine_name FROM maintenance_alerts a
           JOIN machines m ON m.machine_id = a.machine_id
           ORDER BY a.generated_at DESC""",
        fetch=True,
    )
    conn.close()
    return jsonify(rows)


@app.route("/api/alerts/high-risk", methods=["GET"])
def high_risk_alerts():
    conn = get_connection()
    rows = query(
        conn,
        """SELECT a.*, m.machine_name FROM maintenance_alerts a
           JOIN machines m ON m.machine_id = a.machine_id
           WHERE a.risk_level = 'high'
           ORDER BY a.generated_at DESC""",
        fetch=True,
    )
    conn.close()
    return jsonify(rows)


@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "predictive-maintenance-system"})


if __name__ == "__main__":
    app.run(debug=True, port=5004)
