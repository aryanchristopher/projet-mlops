#!/bin/bash
set -e

echo "🚀 Démarrage du déploiement MLOps..."

# 1. Lancer l'infrastructure (Tofu)
echo "🏗️  Phase 1 : Provisionnement Infrastructure (OpenTofu)..."
cd tofu
tofu init
tofu apply -auto-approve
cd ..

# 2. Attente de sécurité (Mises à jour AWS)
echo "⏳ Phase 2 : Attente de 3 minutes (Initialisation AWS)..."
sleep 180

# 3. Configuration (Ansible)
echo "⚙️  Phase 3 : Configuration des serveurs (Ansible)..."
cd ansible
# On lance tout d'un coup
ansible-playbook -i inventory.yml playbook-api.yml playbook-monitoring.yml --ssh-common-args='-o StrictHostKeyChecking=no'
cd ..

echo "✅ DÉPLOIEMENT TERMINÉ !"
echo "-----------------------------------------------------"
# On utilise -A 2 pour descendre de 2 lignes et attraper l'IP
MONITORING_IP=$(grep -A 2 'monitoring:' ansible/inventory.yml | tail -n 1 | awk '{print $1}' | tr -d ':')
API_IP=$(grep -A 2 'api:' ansible/inventory.yml | tail -n 1 | awk '{print $1}' | tr -d ':')

echo "📊 Grafana    : http://$MONITORING_IP:3000"
echo "📈 Prometheus : http://$MONITORING_IP:9090"
echo "🔮 API        : http://$API_IP:5000/docs"
echo "-----------------------------------------------------"
