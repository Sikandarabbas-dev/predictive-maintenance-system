# 🛠️ Predictive Maintenance System
A backend system that ingests machine sensor readings (runtime hours,
temperature, vibration, pressure) and predicts **failure risk before a
breakdown happens** — the core pattern behind industrial IoT + Machine
Learning maintenance platforms used in manufacturing, energy, and
logistics.

---

## 📌 Key Features

- 🔧 Register and manage machines with reading history
- 📊 Log real-time sensor data (runtime, temperature, vibration, pressure)
- 🤖 ML-based failure risk prediction using a **Random Forest classifier**
- 🧠 Graceful **rule-based fallback** when there isn't enough labeled
  failure data yet — the API always returns a usable risk score
- 🚨 Automatic maintenance alert generation with `low / medium / high`
  risk levels
- 💾 Works out-of-the-box with **SQLite** (zero setup) or scales to
  **MySQL** for production
- 🧪 Includes a sample-data generator to simulate machines wearing
  toward failure vs. staying healthy — runnable end-to-end in minutes

---

## 🏗️ Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│  Sensor Data │ ---> │  Flask REST  │ ---> │  MySQL Database  │
│  / IoT Feed  │      │     API      │      │ (machines/       │
└─────────────┘      │  (app.py)    │      │  readings/alerts)│
                      └──────┬───────┘      └─────────────────┘
                             │
                             v
                   ┌───────────────────┐
                   │  ML Risk Model     │
                   │  (Random Forest    │
                   │  classifier)       │
                   └───────────────────┘
```

| Layer | File(s) | Responsibility |
|---|---|---|
| **API layer** | `app.py` | Flask REST API — register machines, log sensor readings, request failure-risk predictions, pull maintenance alerts |
| **Data layer** | `db.py`, `schema.sql` | MySQL schema for machines, reading history, and alerts. Built-in SQLite fallback (`USE_SQLITE_FALLBACK=true`) for instant local testing |
| **ML layer** | `ml/maintenance_model.py` | Random Forest classifier trained on pooled historical readings (runtime hours, temperature, vibration, pressure → failure yes/no), producing a 0–100 failure risk score |

---

## 🧰 Tech Stack

| Category | Tools |
|---|---|
| Backend | Python, Flask |
| Machine Learning | scikit-learn (Random Forest Classifier), NumPy |
| Database | MySQL (production), SQLite (local/demo) |
| API Testing | Postman / cURL |

---

## ⚙️ Setup & Installation

```bash
pip install -r requirements.txt

# Option A: quick demo (default) — uses local SQLite, no MySQL setup needed
python app.py

# Option B: real MySQL
mysql -u root -p < schema.sql
export USE_SQLITE_FALLBACK=false
export DB_HOST=localhost DB_USER=root DB_PASSWORD=yourpass DB_NAME=predictive_maintenance_db
python app.py
```

Server runs at `http://localhost:5004`.

---

## 🚀 Try It End-to-End

```bash
python sample_data/generate_sample_data.py
```

This simulates **3 machines over 60 days** of sensor readings — two
that wear toward failure, one that stays healthy — then requests a
live risk prediction for each.

**Sample output:**
```
Compressor Unit A    -> risk=66.0%  level=medium (source: ml_model)
Pump Station B       -> risk=0.67%  level=low    (source: ml_model)
Conveyor Motor C     -> risk=62.67% level=medium (source: ml_model)
```

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/machines` | Register a machine |
| GET  | `/api/machines` | List machines |
| POST | `/api/readings` | Log a sensor reading (optionally `failed: 1`) |
| GET  | `/api/readings/<machine_id>` | Reading history for a machine |
| POST | `/api/predict/<machine_id>` | Predict current failure risk |
| GET  | `/api/alerts` | List all generated maintenance alerts |
| GET  | `/api/alerts/high-risk` | Machines currently at high risk |

**Log a sensor reading:**
```bash
curl -X POST http://localhost:5004/api/readings \
  -H "Content-Type: application/json" \
  -d '{"machine_id":1,"reading_date":"2026-08-19","runtime_hours":1650,"temperature":82,"vibration":3.8,"pressure":6.1,"failed":0}'
```

**Get a risk prediction:**
```bash
curl -X POST http://localhost:5004/api/predict/1
```

---

## 🧠 How the Model Works

1. Each historical sensor reading is labeled `failed` (0/1) — whether
   a failure occurred at/around that reading.
2. Features (`runtime_hours`, `temperature`, `vibration`, `pressure`)
   are pooled across **all** machines and used to train a Random
   Forest classifier — a shared health model that generalizes across
   similar equipment rather than needing enough failure history per
   individual machine.
3. For a live risk check, the machine's most recent reading is scored
   by the model; `failure_risk` is the predicted probability of
   failure (0–100), bucketed into `low` / `medium` / `high`.
4. Every prediction is persisted to `maintenance_alerts` for an audit
   trail and trend tracking over time.
5. If there isn't yet enough labeled failure data to train on (e.g. a
   brand-new deployment with no failure history), the system falls
   back to a **transparent, weighted rule-based risk score** instead
   of erroring out — so the API always returns a usable result.

---

## 🔭 Possible Extensions

- Time-series features (rate of change in vibration/temperature, not
  just current snapshot values)
- Per-machine-type models once enough data exists per category
- Email/SMS alerting when a machine crosses into `high` risk
- Integration with real IoT sensor feeds (MQTT ingestion) instead of
  manual reading POSTs

---

## 📁 Project Structure

```
predictive-maintenance-system/
├── app.py                  # Flask REST API
├── db.py                   # DB connection + SQLite fallback
├── schema.sql               # MySQL schema
├── requirements.txt
├── ml/
│   └── maintenance_model.py # Random Forest risk model + rule-based fallback
├── sample_data/
│   └── generate_sample_data.py
└── README.md

## 📄 License

This project is acadm.
