from fastapi import FastAPI, Response
from pydantic import BaseModel
import joblib
import os

from prometheus_client import Counter, Histogram, generate_latest

app = FastAPI()

# Chemin vers le modèle
BASE_DIR = os.path.dirname(__file__)
MODEL_PATH = os.path.join(BASE_DIR, "model", "model.pkl")

# Tenter de charger le modèle
model = None
if os.path.exists(MODEL_PATH):
    try:
        model = joblib.load(MODEL_PATH)
    except Exception as e:
        print("Erreur lors du chargement du modèle :", e)

# --- METRIQUES PROMETHEUS ---
PREDICTION_COUNT = Counter(
    "prediction_requests_total",
    "Nombre total de requetes sur /predict"
)
PREDICTION_LATENCY = Histogram(
    "prediction_latency_seconds",
    "Latence des requetes /predict en secondes"
)


class InputData(BaseModel):
    x1: float
    x2: float
    x3: float


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "model_loaded": model is not None
    }


@app.post("/predict")
def predict(data: InputData):
    # Incrémenter le compteur d'appels
    PREDICTION_COUNT.inc()

    # Mesurer la latence de la prédiction
    with PREDICTION_LATENCY.time():
        features = [[data.x1, data.x2, data.x3]]

        # Fallback si pas de modèle réel
        if model is None:
            score = data.x1 * 0.5 + data.x2 * 0.3 + data.x3 * 0.2
            return {
                "prediction": score,
                "model": "dummy"
            }

        # Si modèle réel dispo
        pred = model.predict(features)[0]
        return {
            "prediction": float(pred),
            "model": "mlflow"
        }


@app.get("/metrics")
def metrics():
    """Endpoint exposé pour Prometheus"""
    data = generate_latest()
    return Response(content=data, media_type="text/plain; version=0.0.4")

