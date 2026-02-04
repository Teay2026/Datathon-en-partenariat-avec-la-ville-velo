#!/usr/bin/env bash
set -euo pipefail

INCOMING="data/bronze/_incoming"
AMEN_DIR="data/bronze/amenagements"
SITE_DIR="data/bronze/comptage/sites"
CHAN_DIR="data/bronze/comptage/channels"
MEAS_DIR="data/bronze/comptage/measures"

mkdir -p "$INCOMING" "$AMEN_DIR" "$SITE_DIR" "$CHAN_DIR" "$MEAS_DIR"

echo "📥 Place tes CSV bruts dans: $INCOMING"
echo "   Puis renomme-les comme ci-dessous (ou adapte les patterns dans ce script)."
echo ""

# Adapte les patterns si tes fichiers ont d'autres noms
# - aménagements : amenagements*.csv ou amenagements*.geojson
# - sites : sites*.csv
# - channels : channels*.csv
# - measures : measures*.csv (ou plusieurs fichiers measures_*.csv)

shopt -s nullglob

# Aménagements (CSV ou GeoJSON)
for f in "$INCOMING"/amenagements*.csv "$INCOMING"/amenagements*.geojson; do
  echo "➡️  Copy $f -> $AMEN_DIR/"
  cp -f "$f" "$AMEN_DIR/"
done

# Sites
for f in "$INCOMING"/sites*.csv; do
  echo "➡️  Copy $f -> $SITE_DIR/sites.csv"
  cp -f "$f" "$SITE_DIR/sites.csv"
done

# Channels
for f in "$INCOMING"/channels*.csv; do
  echo "➡️  Copy $f -> $CHAN_DIR/channels.csv"
  cp -f "$f" "$CHAN_DIR/channels.csv"
done

# Measures (1 gros fichier ou plusieurs)
count=0
for f in "$INCOMING"/measures*.csv "$INCOMING"/mesures*.csv; do
  echo "➡️  Copy $f -> $MEAS_DIR/"
  cp -f "$f" "$MEAS_DIR/"
  count=$((count+1))
done

if [ "$count" -eq 0 ]; then
  echo "⚠️  Aucun fichier measures trouvé dans $INCOMING (pattern measures*.csv)."
  echo "   Mets tes fichiers measures ici ou adapte les patterns."
fi

echo ""
echo "✅ BRONZE prêt :"
echo " - $AMEN_DIR"
echo " - $SITE_DIR/sites.csv"
echo " - $CHAN_DIR/channels.csv"
echo " - $MEAS_DIR/"
