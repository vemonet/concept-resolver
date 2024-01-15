#!/bin/bash

if [ "$1" = "--no-cache" ]; then
    echo "📦️ Building without cache"
    ssh ids3 'cd /data/deploy-services/concept-resolver ; git pull ; docker compose build --no-cache ; docker compose down ; docker compose up --force-recreate -d'
else
    echo "♻️  Building with cache"
    ssh ids3 'cd /data/deploy-services/concept-resolver ; git pull ; docker compose up --force-recreate --build -d'
fi
