# Module 2 (Spatial Usage) — Data Requirements

**To:** Module 1 Developer (Bronze → Silver)  
**From:** Module 2 Developer (Spatial Usage)  
**Date:** December 19, 2025

This document specifies exactly what Silver tables and columns Module 2 needs to perform spatial linking and flow aggregation.

---

## Required Silver Tables

### 1. `silver_amenagements` (Infrastructure)

**Purpose:** Locate bike infrastructure for spatial matching with counters

**Required Columns:**

| Column | Type | Required? | Notes |
|--------|------|-----------|-------|
| `amenagement_id` | string | ✅ CRITICAL | Primary key, must be unique |
| `centroid_lat` | float | ✅ CRITICAL | Latitude for spatial join (200m buffer) |
| `centroid_lon` | float | ✅ CRITICAL | Longitude for spatial join (200m buffer) |
| `annee_livraison` | int | ⚠️ OPTIONAL | Useful for Module 3 (scoring), but not used in Module 2 |
| `geom_wkt` | string | ⚠️ OPTIONAL | Nice to have for visualization, not used in spatial join |
| `type_amenagement` | string | ⚠️ OPTIONAL | For analysis/reporting |
| `longueur_m` | float | ⚠️ OPTIONAL | For analysis/reporting |
| `commune` | string | ⚠️ OPTIONAL | For analysis/reporting |

**Data Quality Requirements:**
- ✅ No NULL values in `amenagement_id`, `centroid_lat`, `centroid_lon`
- ✅ Coordinates must be in WGS84 (decimal degrees)
- ✅ Lyon area expected: lat ~45.7-45.8, lon ~4.8-4.9
- ✅ No duplicate `amenagement_id`

---

### 2. `silver_sites` (Counter Locations)

**Purpose:** Locate physical counter sites for spatial matching

**Required Columns:**

| Column | Type | Required? | Notes |
|--------|------|-----------|-------|
| `site_id` | string | ✅ CRITICAL | Primary key, must be unique |
| `lat` | float | ✅ CRITICAL | Latitude for spatial join |
| `lon` | float | ✅ CRITICAL | Longitude for spatial join |
| `commune` | string | ⚠️ OPTIONAL | For analysis/reporting |

**Data Quality Requirements:**
- ✅ No NULL values in `site_id`, `lat`, `lon`
- ✅ Coordinates must be in WGS84 (decimal degrees)
- ✅ No duplicate `site_id`

---

### 3. `silver_channels` (Counter Channels)

**Purpose:** Link sites to specific counting channels and filter for bike mode

**Required Columns:**

| Column | Type | Required? | Notes |
|--------|------|-----------|-------|
| `channel_id` | string | ✅ CRITICAL | Primary key, must be unique |
| `site_id` | string | ✅ CRITICAL | Foreign key to `silver_sites.site_id` |
| `mode` | string | ✅ CRITICAL | Must contain "velo" for bike channels (filter value in config.yml) |
| `sens` | string | ⚠️ OPTIONAL | Direction (Nord, Sud, Est, Ouest) — useful for analysis |

**Data Quality Requirements:**
- ✅ No NULL values in `channel_id`, `site_id`, `mode`
- ✅ All `site_id` values must exist in `silver_sites`
- ✅ `mode` should be normalized (e.g., all lowercase "velo" or consistent casing)
- ✅ No duplicate `channel_id`

**Important:** Make sure the `mode` value for bikes matches the config setting (`bike_mode_value: "velo"` in config.yml). If the raw data uses different values (e.g., "vélo", "bicycle", "bike"), normalize to "velo".

---

### 4. `silver_measures` (Time-Series Counts)

**Purpose:** Daily bike flow data to aggregate per infrastructure

**Required Columns:**

| Column | Type | Required? | Notes |
|--------|------|-----------|-------|
| `channel_id` | string | ✅ CRITICAL | Foreign key to `silver_channels.channel_id` |
| `date` | date | ✅ CRITICAL | Date of measurement (for daily aggregation) |
| `flux` | int | ✅ CRITICAL | Number of bike passages |
| `is_valid` | boolean | ✅ CRITICAL | Data quality flag (filter out invalid) |
| `ts` | timestamp | ⚠️ OPTIONAL | Precise timestamp — not needed for daily aggregation |

**Data Quality Requirements:**
- ✅ No NULL values in `channel_id`, `date`, `flux`, `is_valid`
- ✅ All `channel_id` values must exist in `silver_channels`
- ✅ `flux` should be non-negative integers
- ✅ Date range should cover before/after infrastructure delivery dates
- ✅ Handle duplicates: If multiple measures per channel/date, aggregate in Module 1 (sum flux per day)

**Critical:** If raw data has hourly/sub-daily measures, please **aggregate to daily level** in Module 1 (sum flux per channel per day). Module 2 expects one row per channel per date.

---

## Spatial Join Logic (Module 2)

Here's how Module 2 will use this data:

```python
# 1. Calculate distance between infrastructure and counter sites
distance = haversine(amenagement.centroid_lat, amenagement.centroid_lon,
                     site.lat, site.lon)

# 2. Keep only pairs within 200m buffer
if distance <= 200:
    link = (amenagement_id, site_id)

# 3. Join with channels and filter bike mode
channels_for_amen = channels[channels.site_id == site_id AND 
                              channels.mode == "velo"]

# 4. Aggregate daily flows
for each (amenagement_id, date):
    flux_estime = SUM(measures.flux) WHERE channel_id IN channels_for_amen
                                        AND measures.date == date
                                        AND measures.is_valid == True
```

---

## Expected Data Volumes (Rough Estimates)

Give me a heads-up if actual volumes are very different:

- **Amenagements:** ~100-500 rows (bike lanes in Lyon metro)
- **Sites:** ~50-200 rows (counter locations)
- **Channels:** ~100-400 rows (multiple channels per site)
- **Measures:** ~100K-1M rows (years of daily data × channels)

---

## File Format & Location

**Expected output from Module 1:**

```
data/silver/
├── silver_amenagements/  (Parquet format)
├── silver_sites/         (Parquet format)
├── silver_channels/      (Parquet format)
└── silver_measures/      (Parquet format)
```

**Why Parquet?**
- Columnar format = fast filtering
- Schema enforcement
- Compression
- Native Spark support

---

## Questions to Discuss

Before you start Module 1, let's align on:

1. **Mode values:** What exact strings appear in the raw data for bikes? ("velo", "vélo", "bike"?)
2. **Date format:** Are there any missing dates or gaps in the time series?
3. **Measure granularity:** Is raw data hourly, daily, or other? Should you aggregate to daily?
4. **Coordinate system:** Are raw coordinates in WGS84, or do they need transformation?
5. **Invalid data:** What makes a measure invalid? (`is_valid = False`)

---

## Contact & Coordination

Once you have questions or sample data ready, let's do a quick sync to validate:

1. Share 5-10 rows of each table as CSV
2. I'll verify schemas match
3. We both test with the sample data
4. Then you process the full dataset

**My Mock Data:** I've already created mock Silver data following these specs in `notebooks/02_spatial_usage_exploration.ipynb`. You can use that as a reference for expected schema and data types.

---

**Bottom Line:** I need clean lat/lon coordinates, bike channel IDs, and daily flow counts. Everything else is bonus! 🚴
