"""
Script: Ajouter les coordonnées géométriques aux aménagements
─────────────────────────────────────────────────────────────
Input:
  - data/silver/silver_amenagements/ (Parquet)
  - data/bronze/metropole-de-lyon_pvo_patrimoine_voirie.pvoamenagementcyclable.json
  
Output:
  - data/silver/silver_amenagements_with_coordinates/ (Parquet)
  
Nouvelle colonne:
  - coordiantes: string JSON contenant [[lon, lat], [lon, lat], ...]
"""

import json
import yaml
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, FloatType

# ═════════════════════════════════════════════════════════════
# 1. CONFIGURATION
# ═════════════════════════════════════════════════════════════

# Chargement config
with open("config/config.yml") as f:
    config = yaml.safe_load(f)

BRONZE_DIR = config["paths"]["bronze_dir"]
SILVER_DIR = config["paths"]["silver_dir"]

INPUT_PARQUET = f"{SILVER_DIR}/silver_amenagements"
INPUT_JSON = f"{BRONZE_DIR}/metropole-de-lyon_pvo_patrimoine_voirie.pvoamenagementcyclable.json"
OUTPUT_PARQUET = f"{SILVER_DIR}/silver_amenagements_with_coordinates"

print("="*70)
print("🚴 EXTRACTION DES COORDONNÉES GÉOMÉTRIQUES")
print("="*70)

# ═════════════════════════════════════════════════════════════
# 2. INITIALISATION SPARK
# ═════════════════════════════════════════════════════════════

spark = SparkSession.builder \
    .appName("AddGeometryCoordinates") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

print("\n✓ Spark session initialized")

# ═════════════════════════════════════════════════════════════
# 3. CHARGEMENT DES DONNÉES
# ═════════════════════════════════════════════════════════════

# Charger le Parquet en Pandas
df_amenagements = spark.read.parquet(INPUT_PARQUET).toPandas()
print(f"✓ Loaded Parquet: {len(df_amenagements):,} amenagements")
print(f"  Columns: {list(df_amenagements.columns)}")

# Charger le JSON
print(f"\n✓ Loading GeoJSON: {INPUT_JSON}")
with open(INPUT_JSON, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

print(f"✓ Loaded {len(geojson_data['features'])} features from GeoJSON")

# ═════════════════════════════════════════════════════════════
# 4. CRÉER UN DICTIONNAIRE GID → COORDONNÉES
# ═════════════════════════════════════════════════════════════

def extract_coordinates_from_multilinestring(geometry):
    """
    Extrait toutes les coordonnées d'un MultiLineString.
    Retourne une liste de listes: [[[lon, lat], [lon, lat], ...], [[lon, lat], ...]]
    """
    if geometry is None or geometry.get('type') != 'MultiLineString':
        return None
    
    # MultiLineString contient plusieurs LineStrings
    # Chaque LineString est une liste de coordonnées [lon, lat]
    coordinates = geometry.get('coordinates', [])
    
    # On retourne directement la liste de segments
    # Format: [[[lon1, lat1], [lon2, lat2], ...], [[lon3, lat3], ...]]
    return coordinates

# Construire le dictionnaire gid → (nom, coordonnées_json)
geom_dict = {}

for feature in geojson_data['features']:
    gid = feature['properties'].get('gid')
    nom = feature['properties'].get('nom', '')
    geometry = feature.get('geometry')
    
    if gid is not None:
        coords = extract_coordinates_from_multilinestring(geometry)
        if coords:
            # Convertir en JSON string
            coords_json = json.dumps(coords, ensure_ascii=False)
            geom_dict[gid] = {
                'nom': nom,
                'coordiantes': coords_json
            }

print(f"✓ Extracted coordinates for {len(geom_dict):,} features")

# ═════════════════════════════════════════════════════════════
# 5. AJOUTER LA COLONNE AVEC PANDAS
# ═════════════════════════════════════════════════════════════

print("\n✓ Adding 'coordiantes' column...")

def get_coordinates_for_row(row):
    """Obtenir les coordonnées pour un aménagement donné."""
    amenagement_id = row['amenagement_id']
    
    # Essayer de convertir en int
    try:
        gid = int(amenagement_id)
    except (ValueError, TypeError):
        gid = amenagement_id
    
    if gid in geom_dict:
        return geom_dict[gid]['coordiantes']
    return None

# Appliquer la fonction à chaque ligne
df_amenagements['coordiantes'] = df_amenagements.apply(get_coordinates_for_row, axis=1)

# Statistiques
total_count = len(df_amenagements)
coords_count = df_amenagements['coordiantes'].notna().sum()
missing_count = total_count - coords_count

print(f"\n📊 Statistiques:")
print(f"  • Total aménagements: {total_count:,}")
print(f"  • Avec coordonnées: {coords_count:,} ({coords_count/total_count*100:.1f}%)")
print(f"  • Sans coordonnées: {missing_count:,} ({missing_count/total_count*100:.1f}%)")

# ═════════════════════════════════════════════════════════════
# 6. SAUVEGARDER LE RÉSULTAT
# ═════════════════════════════════════════════════════════════

print(f"\n✓ Saving to: {OUTPUT_PARQUET}")

# S'assurer que la colonne coordiantes est bien de type string
# Forcer explicitement le type pour éviter toute troncature
df_amenagements['coordiantes'] = df_amenagements['coordiantes'].astype(str)

# Vérifier avant sauvegarde
print(f"  Vérification avant sauvegarde:")
sample_check = df_amenagements[df_amenagements['coordiantes'].notna()].iloc[0]
coords_len = len(sample_check['coordiantes'])
print(f"  Exemple longueur: {coords_len} caractères")
if coords_len < 100:
    print(f"  ⚠️ ATTENTION: Longueur suspecte!")

# Sauvegarder directement en Parquet avec Pandas
# Utiliser compression 'snappy' pour éviter les problèmes de troncature
df_amenagements.to_parquet(
    OUTPUT_PARQUET, 
    engine='pyarrow', 
    index=False,
    compression='snappy'
)

print(f"✓ Saved successfully!")
print(f"  → Columns: {list(df_amenagements.columns)}")

# Vérification post-sauvegarde
print(f"\n🔍 Vérification post-sauvegarde:")
df_verify = pd.read_parquet(OUTPUT_PARQUET)
sample_verify = df_verify[df_verify['coordiantes'].notna()].iloc[0]
verify_len = len(sample_verify['coordiantes'])
print(f"  Longueur après lecture: {verify_len} caractères")

if verify_len == coords_len:
    print(f"  ✅ Données intactes après sauvegarde!")
else:
    print(f"  ❌ PROBLÈME: Troncature détectée ({coords_len} → {verify_len})")

# ═════════════════════════════════════════════════════════════
# 7. VÉRIFICATION & APERÇU
# ═════════════════════════════════════════════════════════════

print("\n" + "="*70)
print("🔍 APERÇU DES RÉSULTATS")
print("="*70)

# Montrer quelques exemples avec coordonnées
sample_with_coords = df_amenagements[df_amenagements['coordiantes'].notna()].head(3)

print("\n✅ Exemples avec coordonnées:")
for idx, row in sample_with_coords.iterrows():
    print(f"\n  ID: {row['amenagement_id']}")
    print(f"  Nom: {row['nom']}")
    print(f"  Longueur string JSON: {len(row['coordiantes'])} caractères")
    
    # Vérifier que le JSON est valide et complet
    try:
        coords_parsed = json.loads(row['coordiantes'])
        total_points = sum(len(segment) for segment in coords_parsed)
        print(f"  Nombre de segments: {len(coords_parsed)}")
        print(f"  Nombre total de points: {total_points}")
        
        # Vérifier la complétude
        if row['coordiantes'].endswith('...'):
            print(f"  ❌ ATTENTION: Données tronquées!")
        else:
            print(f"  ✅ JSON complet et valide")
            
        # Afficher preview court
        coords_preview = row['coordiantes'][:100] + "..." if len(row['coordiantes']) > 100 else row['coordiantes']
        print(f"  Preview: {coords_preview}")
    except json.JSONDecodeError as e:
        print(f"  ❌ ERREUR JSON: {e}")
        print(f"  Derniers caractères: ...{row['coordiantes'][-50:]}")
        pass

# Montrer les aménagements sans coordonnées
if missing_count > 0:
    print("\n⚠️ Exemples SANS coordonnées:")
    sample_missing = df_amenagements[df_amenagements['coordiantes'].isna()].head(5)
    for idx, row in sample_missing.iterrows():
        print(f"  ID: {row['amenagement_id']}, Nom: {row['nom']}")

print("\n" + "="*70)
print("✅ TERMINÉ")
print("="*70)
print(f"\n📁 Fichier de sortie: {OUTPUT_PARQUET}")
print(f"📊 {coords_count:,}/{total_count:,} aménagements avec coordonnées")

spark.stop()
