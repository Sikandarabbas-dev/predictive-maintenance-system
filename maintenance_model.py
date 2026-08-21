"""
Predictive maintenance model.

Approach: binary classification (RandomForest) trained on historical
sensor readings labeled with whether a failure occurred at/after that
reading. Features: runtime_hours since last maintenance, temperature,
vibration, pressure — the standard signal set for rotating/industrial
equipment health monitoring.

Trained globally across all machines' historical readings (pooled),
which works well once several machines have contributed history; for
a single always-healthy machine there's no failure signal to learn
from; the API surfaces a rule-based fallback risk score in that case
so /api/predict still degrades gracefully rather than failing outright.
"""

import numpy as np
from sklearn.ensemble import RandomForestClassifier

FEATURE_ORDER = ["runtime_hours", "temperature", "vibration", "pressure"]


def _rule_based_risk(features):
    """
    Fallback heuristic used only when there isn't enough labeled failure
    data yet to train a model. Simple weighted threshold scoring based
    on how far each reading is from a "normal" operating band.
    """
    runtime_hours, temperature, vibration, pressure = features
    score = 0.0
    score += min(runtime_hours / 2000, 1.0) * 35       # wear from accumulated runtime
    score += max(0, (temperature - 70) / 30) * 25        # overheating
    score += max(0, (vibration - 2.5) / 3) * 25           # excess vibration
    score += max(0, abs(pressure - 5.0) - 1.0) / 3 * 15   # pressure drift
    return round(min(max(score, 0), 100), 2)


class PredictiveMaintenanceModel:
    def __init__(self):
        self.model = RandomForestClassifier(
            n_estimators=150, max_depth=6, random_state=42, class_weight="balanced"
        )
        self.fitted = False
        self.has_both_classes = False

    def fit(self, readings):
        """
        readings: list of dicts with keys runtime_hours, temperature,
                  vibration, pressure, failed (0/1)
        """
        if len(readings) < 10:
            self.fitted = False
            return self

        X = np.array([[r[f] for f in FEATURE_ORDER] for r in readings])
        y = np.array([int(r["failed"]) for r in readings])

        if len(set(y)) < 2:
            # no failure examples yet to learn from — model can't be trained meaningfully
            self.fitted = False
            self.has_both_classes = False
            return self

        self.model.fit(X, y)
        self.fitted = True
        self.has_both_classes = True
        return self

    def predict_risk(self, runtime_hours, temperature, vibration, pressure):
        features = [runtime_hours, temperature, vibration, pressure]

        if self.fitted and self.has_both_classes:
            proba = self.model.predict_proba([features])[0]
            classes = list(self.model.classes_)
            failure_prob = proba[classes.index(1)] if 1 in classes else 0.0
            risk = round(float(failure_prob) * 100, 2)
            source = "ml_model"
        else:
            risk = _rule_based_risk(features)
            source = "rule_based_fallback"

        if risk >= 70:
            level = "high"
        elif risk >= 35:
            level = "medium"
        else:
            level = "low"

        return {"failure_risk": risk, "risk_level": level, "score_source": source}
