FROM python:3.10-slim

WORKDIR /app

# Copier les fichiers de l'API
COPY . /app

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Exposer le port de l'API
EXPOSE 5000

# Commande de démarrage
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

