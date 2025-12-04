from fastapi import FastAPI
from pydantic import BaseModel
import joblib
import os

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


class InputData(BaseModel):
    x1: float
    x2: float
    x3: float


@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None
    }


@app.post("/predict")
def predict(data: InputData):
    features = [[data.x1, data.x2, data.x3]]

    # Si modèle réel indisponible → fallback dummy
    if model is None:
        score = data.x1 * 0.5 + data.x2 * 0.3 + data.x3 * 0.2
        return {
            "prediction": score,
            "model": "dummy"
        }

    # Si modèle présent → prédiction réelle
    pred = model.predict(features)[0]
    return {
        "prediction": float(pred),
        "model": "mlflow"
    }

