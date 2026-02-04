#!/usr/bin/env bash
set -euo pipefail

./scripts/run_silver.sh
./scripts/run_usage.sh
./scripts/run_scoring.sh

echo "✅ Pipeline complet terminé."
echo "📦 Exports Leaflet attendus dans: exports/leaflet/"
