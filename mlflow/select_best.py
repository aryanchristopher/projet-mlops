import os
import json
import mlflow
import mlflow.sklearn

EXPERIMENT_NAME = "breast_cancer_multi_models"
EXPORT_PATH = os.path.join("..", "api", "model")  # api/model/


def get_best_run():
    """
    Récupère le meilleur run de l’expérience selon la métrique val_accuracy.
    """
    experiment = mlflow.get_experiment_by_name(EXPERIMENT_NAME)
    if experiment is None:
        raise ValueError(
            f"L’expérience MLflow '{EXPERIMENT_NAME}' n’existe pas. "
            f"Lance d’abord train.py pour générer des runs."
        )

    # Tous les runs triés par val_accuracy décroissante
    runs = mlflow.search_runs(
        experiment_ids=[experiment.experiment_id],
        order_by=["metrics.val_accuracy DESC"]
    )

    if runs.empty:
        raise ValueError("Aucun run trouvé pour cette expérience.")

    return runs.iloc[0]


def export_best_model():
    """
    Charge le meilleur modèle via MLflow et l’exporte dans ../api/model.
    Écrit aussi un fichier metadata.json avec run_id, accuracy, etc.
    """
    best_run = get_best_run()
    best_run_id = best_run.run_id
    best_accuracy = best_run["metrics.val_accuracy"]
    best_model_name = best_run["params.model_name"]

    print("🏆 Meilleur run trouvé :")
    print(f"   - run_id       = {best_run_id}")
    print(f"   - model_name   = {best_model_name}")
    print(f"   - val_accuracy = {best_accuracy:.4f}")

    # Chemin MLflow pour le modèle logué dans train.py
    model_uri = f"runs:/{best_run_id}/model"

    # On charge le modèle
    model = mlflow.sklearn.load_model(model_uri)

    # On s’assure que le dossier d’export existe
    os.makedirs(EXPORT_PATH, exist_ok=True)

    # On exporte le modèle au format MLflow dans api/model
    mlflow.sklearn.save_model(model, path=EXPORT_PATH)
    print(f"📦 Modèle exporté au format MLflow dans : {EXPORT_PATH}")

    # Fichier metadata.json
    metadata = {
        "best_run_id": best_run_id,
        "val_accuracy": float(best_accuracy),
        "experiment_name": EXPERIMENT_NAME,
        "model_name": best_model_name,
    }
    metadata_path = os.path.join(EXPORT_PATH, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"📝 Metadata enregistrée dans : {metadata_path}")


if __name__ == "__main__":
    export_best_model()
