import mlflow
import mlflow.sklearn
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score
import pandas as pd
from itertools import product


def load_data(test_size=0.2, random_state=42):
    """
    Charge le dataset de cancer du sein et split en train/test.
    """
    data = load_breast_cancer()
    X = pd.DataFrame(data.data, columns=data.feature_names)
    y = pd.Series(data.target, name="target")
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def build_model(model_name: str, params: dict):
    """
    Crée un modèle sklearn en fonction du nom et des paramètres.
    """
    if model_name == "logreg":
        return LogisticRegression(**params)
    elif model_name == "random_forest":
        return RandomForestClassifier(**params)
    elif model_name == "gradient_boosting":
        return GradientBoostingClassifier(**params)
    else:
        raise ValueError(f"Modèle non supporté : {model_name}")


def train_one_run(model_name: str, params: dict):
    """
    Entraîne UN modèle avec les paramètres donnés,
    log dans MLflow et renvoie l'accuracy.
    """
    X_train, X_test, y_train, y_test = load_data()

    with mlflow.start_run():
        # Log du type de modèle
        mlflow.log_param("model_name", model_name)

        # Log de tous les hyperparamètres
        for k, v in params.items():
            mlflow.log_param(k, v)

        # Création + entraînement du modèle
        model = build_model(model_name, params)
        model.fit(X_train, y_train)

        # Prédictions + métrique
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        mlflow.log_metric("val_accuracy", accuracy)

        # Log du modèle lui-même
        mlflow.sklearn.log_model(model, artifact_path="model")

        print(f"[MLflow] Run – model={model_name}, "
              f"params={params}, val_accuracy={accuracy:.4f}")

        return accuracy


def generate_param_grid(param_grid: dict):
    """
    Prend un dict {param: [val1, val2, ...]} et génère toutes les combinaisons possibles.
    Retourne une liste de dicts (une config par dict).
    """
    keys = list(param_grid.keys())
    values = list(param_grid.values())

    combos = []
    for combo in product(*values):
        params = dict(zip(keys, combo))
        combos.append(params)
    return combos


def run_experiments():
    """
    Lance beaucoup d'expériences (plusieurs modèles x beaucoup de paramètres).
    On vise > 100 runs au total.
    """
    mlflow.set_experiment("breast_cancer_multi_models")

    # ===============================
    # 1) Grilles d'hyperparamètres
    # ===============================

    # ----- Régression logistique -----
    logreg_fixed = {
        "solver": "lbfgs",
        "penalty": "l2",
    }
    logreg_grid = {
        "C": [0.001, 0.01, 0.1, 1.0, 10.0],
        "max_iter": [200, 500],
        "fit_intercept": [True, False],
    }
    logreg_param_combos = [
        {**logreg_fixed, **p} for p in generate_param_grid(logreg_grid)
    ]
    # 5 * 2 * 2 = 20 runs

    # ----- Random Forest -----
    rf_fixed = {
        "criterion": "gini",
        "n_jobs": -1,
    }
    rf_grid = {
        "n_estimators": [50, 100, 200, 400],
        "max_depth": [None, 5, 10, 15],
        "min_samples_split": [2, 5],
        "max_features": ["sqrt", "log2"],
    }
    rf_param_combos = [
        {**rf_fixed, **p} for p in generate_param_grid(rf_grid)
    ]
    # 4 * 4 * 2 * 2 = 64 runs

    # ----- Gradient Boosting -----
    gb_fixed = {
        "subsample": 1.0,
    }
    gb_grid = {
        "n_estimators": [50, 100, 150],
        "learning_rate": [0.05, 0.1, 0.2],
        "max_depth": [2, 3],
    }
    gb_param_combos = [
        {**gb_fixed, **p} for p in generate_param_grid(gb_grid)
    ]
    # 3 * 3 * 2 = 18 runs

    # ===============================
    # 2) Boucle sur tous les modèles
    # ===============================
    print("🚀 Lancement des expérimentations MLflow...")

    total_runs = 0

    # LogReg
    for params in logreg_param_combos:
        train_one_run("logreg", params)
        total_runs += 1

    # Random Forest
    for params in rf_param_combos:
        train_one_run("random_forest", params)
        total_runs += 1

    # Gradient Boosting
    for params in gb_param_combos:
        train_one_run("gradient_boosting", params)
        total_runs += 1

    print(f"✅ Expérimentations terminées. Nombre total de runs : {total_runs}")


if __name__ == "__main__":
    run_experiments()
