#!/bin/bash
echo "💥 Destruction de l'infrastructure..."
cd tofu
tofu destroy -auto-approve
cd ..
echo "💀 Tout est éteint."
