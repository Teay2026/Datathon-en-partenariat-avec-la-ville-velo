# scripts/add_centroids_to_amenagements.py

"""
Script pour ajouter centroid_lat et centroid_lon à silver_amenagements
À partir des géométries du fichier GeoJSON Bronze

Note: Utilise Pandas au lieu de PySpark pour éviter les crashes Windows
"""

import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
import pandas as pd
import pyarrow.parquet as pq
from shapely.geometry import shape

# ==========================================
# Configuration
# ==========================================

with open(project_root / "config" / "config.yml") as f:
    config = yaml.safe_load(f)

BRONZE_GEOJSON = project_root / "data" / "bronze" / "metropole-de-lyon_pvo_patrimoine_voirie.pvoamenagementcyclable.json"
SILVER_AMENAGEMENTS_IN = project_root / config["paths"]["silver_dir"] / "silver_amenagements"
SILVER_AMENAGEMENTS_OUT = project_root / config["paths"]["silver_dir"] / "silver_amenagements_with_centroids"

print("🚀 Adding centroid_lat and centroid_lon to silver_amenagements")
print(f"📍 Bronze GeoJSON: {BRONZE_GEOJSON}")
print(f"📦 Silver Input: {SILVER_AMENAGEMENTS_IN}")
print(f"💾 Silver Output: {SILVER_AMENAGEMENTS_OUT}")
print()

# ==========================================
# Step 1: Load Silver Amenagements (Parquet)
# ==========================================

print("=== Step 1: Load Silver Amenagements ===")

# Read Parquet with Pandas
parquet_files = list(SILVER_AMENAGEMENTS_IN.glob("*.parquet"))

if parquet_files:
    df_amenagements = pd.read_parquet(SILVER_AMENAGEMENTS_IN)
    print(f"✓ Loaded Parquet: {len(df_amenagements)} rows")
else:
    # Fallback to CSV
    csv_path = project_root / "data" / "silver_amenagements.csv"
    if csv_path.exists():
        df_amenagements = pd.read_csv(csv_path, sep=";")
        print(f"✓ Loaded CSV: {len(df_amenagements)} rows")
    else:
        print(f"❌ ERROR: No silver_amenagements found")
        sys.exit(1)

print(f"   Columns: {list(df_amenagements.columns)}")

# Check if centroids already exist
if "centroid_lat" in df_amenagements.columns:
    print("⚠️  centroid_lat already exists - will be replaced")
    df_amenagements = df_amenagements.drop(columns=["centroid_lat", "centroid_lon"])

print()

# ==========================================
# Step 2: Extract Centroids from GeoJSON
# ==========================================

print("=== Step 2: Extract Centroids from GeoJSON ===")

if not BRONZE_GEOJSON.exists():
    print(f"❌ ERROR: Bronze GeoJSON not found at {BRONZE_GEOJSON}")
    sys.exit(1)

# Read GeoJSON and extract centroids
with open(BRONZE_GEOJSON, 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

print(f"✓ Loaded GeoJSON with {len(geojson_data['features'])} features")

# Build list of centroids
centroids_data = []

for feature in geojson_data['features']:
    gid = feature['properties']['gid']
    geom = shape(feature['geometry'])
    
    # Calculate centroid
    centroid = geom.centroid
    centroids_data.append({
        'gid': str(gid),
        'centroid_lat': centroid.y,
        'centroid_lon': centroid.x
    })

print(f"✓ Computed {len(centroids_data)} centroids")

# Show sample
for i in range(min(3, len(centroids_data))):
    row = centroids_data[i]
    print(f"   gid={row['gid']} → lat={row['centroid_lat']:.6f}, lon={row['centroid_lon']:.6f}")

print()

# ==========================================
# Step 3: Create Centroids DataFrame
# ==========================================

print("=== Step 3: Create Centroids DataFrame ===")

df_centroids = pd.DataFrame(centroids_data)

print(f"✓ Created centroids DataFrame: {len(df_centroids)} rows")
print(df_centroids.head())
print()

# ==========================================
# Step 4: Join with Silver Amenagements
# ==========================================

print("=== Step 4: Join Amenagements + Centroids ===")

# Ensure types are compatible for join
# amenagement_id (in df_amenagements) should match gid (in df_centroids)
df_amenagements['amenagement_id'] = df_amenagements['amenagement_id'].astype(str)
df_centroids['gid'] = df_centroids['gid'].astype(str)

# Left join to keep all amenagements
# Join on: amenagement_id = gid
df_merged = df_amenagements.merge(
    df_centroids,
    left_on='amenagement_id',
    right_on='gid',
    how='left'
)

# Drop the redundant gid column (keep amenagement_id)
if 'gid' in df_merged.columns:
    df_merged = df_merged.drop(columns=['gid'])

print(f"✓ Merged: {len(df_merged)} rows")

# Check for missing centroids
missing_count = df_merged['centroid_lat'].isna().sum()
if missing_count > 0:
    print(f"⚠️  {missing_count} rows missing centroids")
    print(df_merged[df_merged['centroid_lat'].isna()][['amenagement_id', 'nom']].head(10))
else:
    print("✓ All rows have centroids")

print()

# ==========================================
# Step 5: Validate & Save
# ==========================================

print("=== Step 5: Validate & Save ===")

# Validation: centroid coordinates in Lyon area
lyon_bounds = {
    'lat_min': 45.5, 'lat_max': 46.0,
    'lon_min': 4.5, 'lon_max': 5.2
}

out_of_bounds = (
    (df_merged['centroid_lat'] < lyon_bounds['lat_min']) |
    (df_merged['centroid_lat'] > lyon_bounds['lat_max']) |
    (df_merged['centroid_lon'] < lyon_bounds['lon_min']) |
    (df_merged['centroid_lon'] > lyon_bounds['lon_max'])
).sum()

if out_of_bounds > 0:
    print(f"⚠️  {out_of_bounds} centroids outside Lyon area bounds")
else:
    print("✓ All centroids within Lyon area")

# Show sample
print("\nSample with centroids:")
print(df_merged[['amenagement_id', 'nom', 'centroid_lat', 'centroid_lon']].head(10))

# Save as Parquet
print(f"\n💾 Saving to {SILVER_AMENAGEMENTS_OUT}")

# Remove existing directory if it exists
import shutil
if SILVER_AMENAGEMENTS_OUT.exists():
    print(f"   ⚠️  Removing existing directory...")
    shutil.rmtree(SILVER_AMENAGEMENTS_OUT)

SILVER_AMENAGEMENTS_OUT.mkdir(parents=True, exist_ok=True)

# Save as single parquet file
output_file = SILVER_AMENAGEMENTS_OUT / "data.parquet"
df_merged.to_parquet(output_file, index=False)

print("✓ Saved successfully!")
print()

# ==========================================
# Step 6: Verify Output
# ==========================================

print("=== Step 6: Verify Output ===")

df_verify = pd.read_parquet(SILVER_AMENAGEMENTS_OUT)

print(f"✓ Verified: {len(df_verify)} rows")
print(f"✓ Columns: {list(df_verify.columns)}")

assert "centroid_lat" in df_verify.columns, "centroid_lat missing!"
assert "centroid_lon" in df_verify.columns, "centroid_lon missing!"

print("\n🎉 SUCCESS! silver_amenagements now has centroid_lat and centroid_lon")
print(f"   Ou\nNext steps:")
print("  1. Rename silver_amenagements_with_centroids → silver_amenagements")
print("  2. Or update notebooks to read from silver_amenagements_with_centroids")