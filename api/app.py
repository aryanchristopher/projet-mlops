from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

# Schéma des données envoyées pour la prédiction
class InputData(BaseModel):
    x1: float
    x2: float
    x3: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/predict")
def predict(data: InputData):
    # Calcul simple juste pour tester l'API
    score = data.x1 * 0.5 + data.x2 * 0.3 + data.x3 * 0.2
    return {"prediction": score}

