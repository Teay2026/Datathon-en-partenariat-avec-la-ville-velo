import os
import sys
import json
import shutil
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import DoubleType

# =========================
# UTILS
# =========================
def save_geojson(df_pandas, filename, lat_col="lat", lon_col="lon", properties=[], geometry_col=None):
    """
    Convert Pandas DataFrame to GeoJSON structure and save.
    """
    features = []
    
    for _, row in df_pandas.iterrows():
        props = {prop: row[prop] for prop in properties if prop in row and pd.notnull(row[prop])}
        
        if geometry_col and geometry_col in row and row[geometry_col]:
            coords = row[geometry_col]
            if isinstance(coords, str):
                 try:
                     coords = json.loads(coords)
                 except:
                     continue
            
            geometry = {
                "type": "LineString",
                "coordinates": coords
            }
        else:
            if pd.isnull(row[lat_col]) or pd.isnull(row[lon_col]):
                continue
            geometry = {
                "type": "Point",
                "coordinates": [float(row[lon_col]), float(row[lat_col])]
            }

        feature = {
            "type": "Feature",
            "properties": props,
            "geometry": geometry
        }
        features.append(feature)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=None)
    print(f"✅ Saved GeoJSON: {filename}")

# Force python vars to match driver
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable 
os.environ["PYSPARK_PYTHON"] = sys.executable

spark = (
    SparkSession.builder
    .master("local[*]")
    .appName("Velomenaj_DataViz_Prep")
    .config("spark.driver.memory", "4g")
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")

BASE_DIR = os.getcwd()
OUT_DIR = os.path.join(BASE_DIR, "DataViz", "data")

# --- 1. PREPARE COUNTERS (From Silver) ---
print("--- 1. Processing Counters (Source: Silver) ---")

# 1a. Load Silver Measures (Parquet)
silver_measures_path = os.path.join(BASE_DIR, "data_temp/silver_measures_union2/silver_measures_union")
if not os.path.exists(silver_measures_path):
    print(f"ERROR: Silver measures not found at {silver_measures_path}")
    spark.stop()
    exit(1)

df_silver = spark.read.parquet(f"file://{silver_measures_path}")

# Verify schema has what we need: lat, lon, flux, point_id
# Group by point_id to get Average Volume
# Note: 'flux' is the volume
from pyspark.sql.functions import avg, first

df_counters_agg = df_silver.groupBy("point_id").agg(
    avg("flux").alias("avg_volume"),
    first("lat").alias("lat"),
    first("lon").alias("lon")
)

# 1b. Load Bronze Sites for Names (CSV)
# We need to map point_id -> site_name. 
# In Bronze: channels(id_channel) -> sites(id_site=channel.id_site) -> site_name
# Assumption: Silver 'point_id' corresponds to 'id_channel' from Bronze.
sites_path = os.path.join(BASE_DIR, "data/bronze/comptage/sites/sites.csv")
channels_path = os.path.join(BASE_DIR, "data/bronze/comptage/channels/channels.csv")

df_sites = spark.read.option("header", "true").option("delimiter", ";").csv(f"file://{sites_path}")
df_channels = spark.read.option("header", "true").option("delimiter", ";").csv(f"file://{channels_path}")

# Join Sites & Channels to make a lookup: channel_id -> site_name
# Sites: site_id, site_name
# Channels: likely channel_id, site_id based on typical structure (let's verify if error happens again or check schema, but site_id matches error suggestion)
# Error suggested: [gid, site_id, parent_site_id, fr_insee_code, xlong, ylat, external_ids, infrastructure_type, site_name, lon, lat]
# So we select site_id, site_name
df_sites_clean = df_sites.select(F.col("site_id"), F.col("site_name"))

# Channels: check standard naming. Typically `channel_id` and `site_id`.
# If Silver 'point_id' matches 'channel_id', we alias it.
df_channels_clean = df_channels.select(F.col("channel_id").alias("point_id"), F.col("site_id"))

# Lookup: point_id -> site_name
df_names = df_channels_clean.join(df_sites_clean, "site_id", "inner").select("point_id", "site_name")

# 1c. Join Aggregated Silver Data with Names
df_final_counters = df_counters_agg.join(df_names, "point_id", "left")

# Convert to Pandas for GeoJSON export
pdf_counters = df_final_counters.toPandas()

# Fill missing names
pdf_counters['site_name'] = pdf_counters['site_name'].fillna("Compteur " + pdf_counters['point_id'].astype(str))

# Create GeoJSON
dst_counters = os.path.join(OUT_DIR, "counters.geojson")
save_geojson(pdf_counters, dst_counters, lat_col="lat", lon_col="lon", properties=["site_name", "avg_volume"])


print("--- 2. Processing Amenities (Scored) ---")
# LOAD FEATURES (Coordinates)
df_features = spark.read.parquet(f"file://{BASE_DIR}/data_temp/silver_amenagements_with_coordinates")

def parse_coords_linestring(flat_str):
    if not flat_str: return None
    try:
        clean = flat_str.replace('[', '').replace(']', '').replace('"', '')
        parts = [float(x.strip()) for x in clean.split(',') if x.strip()]
        coords = []
        for i in range(0, len(parts), 2):
            if i+1 < len(parts):
                coords.append([parts[i], parts[i+1]])
        return coords
    except:
        return None

# LOAD SCORES (Global)
df_scores = spark.read.json(f"file://{BASE_DIR}/amenagement_scoring_global_json_2")

# LOAD SCORES (Yearly)
try:
    df_yearly = spark.read.json(f"file://{BASE_DIR}/amenagement_scoring_yearly_json")
    # If using hive partitioning (year=XXXX), 'year' should be a column. 
    # If not, we might need to rely on the file path or schema. 
    # Let's check columns. If 'year' is missing but needed, we trust Spark discovery.
    # Scores table likely has: amenagement_id, score, (year from partition)
    
    # We want a map: year -> score per amenagement_id
    # Ensure year is string for JSON key
    df_yearly_agg = df_yearly.groupBy("amenagement_id").agg(
        F.map_from_entries(
            F.collect_list(
                F.struct(F.col("year").cast("string"), F.col("score").cast(DoubleType()))
            )
        ).alias("yearly_scores")
    )
except Exception as e:
    print(f"⚠️ Could not load yearly scores: {e}")
    df_yearly_agg = None

# features have plain ID, scores have prefix. prediction also has prefix added to features locally.
df_features = df_features.withColumn(
    "amenagement_id_full", 
    F.concat(F.lit("pvo_patrimoine_voirie.pvoamenagementcyclable."), F.col("amenagement_id"))
)

# JOIN Global Score
df_scored_geo = df_features.join(df_scores, df_features.amenagement_id_full == df_scores.amenagement_id, "inner")

# JOIN Yearly Score if available
if df_yearly_agg:
    # Year ID also has prefix? Or numeric? 
    # Usually scoring output keeps input ID format. 
    # But Scoring2 outputs PREFIXED ID. 
    # If yearly scoring was generated similarly to Scoring2, it has PREFIXED ID.
    # Let's assume PREFIXED ID.
    df_scored_geo = df_scored_geo.join(df_yearly_agg, on="amenagement_id", how="left")

df_out = df_scored_geo.select(
    df_scores.amenagement_id, 
    df_scores.score, 
    df_features.nom, 
    df_features.typeamenagement,
    F.col("yearly_scores") if df_yearly_agg else F.lit(None).alias("yearly_scores"),
    F.col("coordiantes").alias("coords_str")
)

pdf_amenities = df_out.toPandas()
pdf_amenities["geometry_coords"] = pdf_amenities["coords_str"].apply(parse_coords_linestring)
pdf_amenities = pdf_amenities.dropna(subset=["geometry_coords"])

save_geojson(pdf_amenities, os.path.join(OUT_DIR, "amenities.geojson"), 
             properties=["amenagement_id", "score", "nom", "typeamenagement", "yearly_scores"], 
             geometry_col="geometry_coords")


print("--- 3. Processing Predictions ---")
src_pred = os.path.join(BASE_DIR, "predictions_heatmap_lyon_2.json")
dst_pred = os.path.join(OUT_DIR, "predictions.geojson")

if os.path.exists(src_pred):
    with open(src_pred, "r") as f:
        preds = json.load(f)

    df_pred = pd.DataFrame(preds)
    save_geojson(df_pred, dst_pred, lat_col="centroid_lat", lon_col="centroid_lon", properties=["prob_success", "recommendation"])
else:
    print(f"WARNING: Predictions file not found at {src_pred}")


print("--- 4. Processing Tension Zones (Gap Analysis) ---")
# Logic: Counters > 100/h AND Nearby Amenities Score < 0.5
HIGH_VOL_THRESHOLD = 100
LOW_SCORE_THRESHOLD = 0.5
DIST_THRESHOLD_DEG = 0.0005 # Approx 50m

# Filter
high_vol_counters = pdf_counters[pdf_counters['avg_volume'] > HIGH_VOL_THRESHOLD]
low_score_amenities = pdf_amenities[pdf_amenities['score'] < LOW_SCORE_THRESHOLD]

tension_features = []

# Simple spatial join
for _, counter in high_vol_counters.iterrows():
    c_lat, c_lon = counter['lat'], counter['lon']
    
    # Check simple bounding box first for speed
    candidates = low_score_amenities[
        (low_score_amenities['geometry_coords'].apply(lambda x: min(p[1] for p in x)) < c_lat + DIST_THRESHOLD_DEG) &
        (low_score_amenities['geometry_coords'].apply(lambda x: max(p[1] for p in x)) > c_lat - DIST_THRESHOLD_DEG) &
        (low_score_amenities['geometry_coords'].apply(lambda x: min(p[0] for p in x)) < c_lon + DIST_THRESHOLD_DEG*1.5) &
        (low_score_amenities['geometry_coords'].apply(lambda x: max(p[0] for p in x)) > c_lon - DIST_THRESHOLD_DEG*1.5)
    ]
    
    if not candidates.empty:
        tension_features.append(candidates)

if tension_features:
    df_tension = pd.concat(tension_features).drop_duplicates(subset=['amenagement_id'])
    print(f"Found {len(df_tension)} tension zones.")
    save_geojson(df_tension, os.path.join(OUT_DIR, "tension.geojson"), 
                 properties=["amenagement_id", "score", "nom"], 
                 geometry_col="geometry_coords")
else:
    print("No tension zones found.")


print("--- 5. Processing Efficiency Stats (Score vs Volume) ---")
# Objective: Avg Score vs Avg Volume per Amenity Type
# 1. We need to assign Volume to Amenities.
#    We already linked High Vol -> Low Score for Tension.
#    Now we want general link.
#    Let's assign each Counter's volume to the NEAREST Amenity (if < 50m).

amenities_with_vol = []
counters_assigned = 0

for _, counter in pdf_counters.iterrows():
    c_lat, c_lon = counter['lat'], counter['lon']
    vol = counter['avg_volume']
    
    # Filter nearby (optimization)
    candidates = pdf_amenities[
        (pdf_amenities['geometry_coords'].apply(lambda x: min(p[1] for p in x)) < c_lat + DIST_THRESHOLD_DEG) &
        (pdf_amenities['geometry_coords'].apply(lambda x: max(p[1] for p in x)) > c_lat - DIST_THRESHOLD_DEG) &
        (pdf_amenities['geometry_coords'].apply(lambda x: min(p[0] for p in x)) < c_lon + DIST_THRESHOLD_DEG*1.5) &
        (pdf_amenities['geometry_coords'].apply(lambda x: max(p[0] for p in x)) > c_lon - DIST_THRESHOLD_DEG*1.5)
    ].copy()
    
    if not candidates.empty:
        # Find nearest
        # Simple Euclidean on coords (approx)
        def get_min_dist(coords):
            return min((((p[0]-c_lon)**2 + (p[1]-c_lat)**2)**0.5) for p in coords)
            
        candidates['dist'] = candidates['geometry_coords'].apply(get_min_dist)
        nearest = candidates.loc[candidates['dist'].idxmin()]
        
        # Assign volume to this amenity instance (we collect them)
        amenities_with_vol.append({
            "typeamenagement": nearest['typeamenagement'],
            "score": nearest['score'],
            "volume": vol
        })
        counters_assigned += 1

print(f"Assigned volume from {counters_assigned}/{len(pdf_counters)} counters to amenities.")

# Convert to DF for aggregation
if amenities_with_vol:
    df_vol = pd.DataFrame(amenities_with_vol)
    
    # We also want to include amenities that DO NOT have volume for the Score Average?
    # The plan said: "Avg Score: Average of score for ALL amenities of this type."
    #                "Avg Volume: Average of volume for amenities of this type THAT HAVE LINKED COUNTERS."
    
    # 1. Avg Score (All amenities)
    grp_score = pdf_amenities.groupby("typeamenagement")["score"].mean().reset_index(name="avg_score")
    
    # 2. Avg Volume (Linked amenities)
    grp_vol = df_vol.groupby("typeamenagement")["volume"].mean().reset_index(name="avg_volume")
    
    # Merge
    df_stats = pd.merge(grp_score, grp_vol, on="typeamenagement", how="left").fillna(0)
    
    # Sort by Score desc
    df_stats = df_stats.sort_values("avg_score", ascending=False)
    
    stats_out = df_stats.to_dict(orient="records")
    
    with open(os.path.join(OUT_DIR, "stats.json"), "w") as f:
        json.dump(stats_out, f, indent=2)
    print("✅ Saved Stats: stats.json")
else:
    print("⚠️ No volume links found for stats.")

spark.stop()
print("Data Preparation Complete.")
