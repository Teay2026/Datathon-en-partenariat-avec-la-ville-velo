# Data Contract — Projet Aménagements Cyclables (Lyon)

Ce document décrit les **schémas des tables** produites par le pipeline Spark.
Il constitue le **contrat de données** entre les différents modules
(ingestion, spatialisation, scoring, visualisation).

---

## 🔹 BRONZE (données brutes)

Les données BRONZE correspondent aux fichiers CSV/GeoJSON bruts
téléchargés depuis Google Drive et copiés localement dans `data/bronze/`.

Aucune transformation métier n’est appliquée à ce stade.

---

## 🔹 SILVER (données nettoyées et normalisées)

### Table : `silver_amenagements`

**Description**  
Aménagements cyclables nettoyés et standardisés.

**Grain**  
1 ligne = 1 aménagement cyclable

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| amenagement_id | string | Identifiant unique de l’aménagement |
| annee_livraison | int | Année de livraison |
| type_amenagement | string | Type d’aménagement |
| environnement | string | Environnement urbain |
| longueur_m | float | Longueur en mètres |
| geom_wkt | string | Géométrie WKT |
| centroid_lat | float | Latitude du centroïde |
| centroid_lon | float | Longitude du centroïde |
| commune | string | Commune (si disponible) |

**Clé primaire**  
- `amenagement_id`

---

### Table : `silver_sites`

**Description**  
Sites physiques des capteurs de comptage.

**Grain**  
1 ligne = 1 site de comptage

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| site_id | string | Identifiant du site |
| lat | float | Latitude |
| lon | float | Longitude |
| commune | string | Commune (si disponible) |

**Clé primaire**  
- `site_id`

---

### Table : `silver_channels`

**Description**  
Canaux de comptage associés aux sites (sens, voie, etc.).

**Grain**  
1 ligne = 1 channel

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| channel_id | string | Identifiant du channel |
| site_id | string | Identifiant du site |
| mode | string | Mode de transport (ex : vélo) |
| sens | string | Sens de circulation (si dispo) |

**Clé primaire**  
- `channel_id`

**Clé étrangère**  
- `site_id` → `silver_sites.site_id`

---

### Table : `silver_measures`

**Description**  
Mesures de comptage temporelles.

**Grain**  
1 ligne = 1 mesure de comptage

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| channel_id | string | Identifiant du channel |
| ts | timestamp | Horodatage |
| date | date | Date |
| flux | int | Nombre de passages |
| is_valid | boolean | Indicateur de validité |

**Clé étrangère**  
- `channel_id` → `silver_channels.channel_id`

---

## 🔹 GOLD — Usage et scoring

### Table : `gold_flow_amenagement_daily`

**Description**  
Flux estimé par aménagement et par jour.

**Grain**  
1 ligne = 1 aménagement × 1 jour

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| amenagement_id | string | Identifiant de l’aménagement |
| date | date | Jour |
| flux_estime | float | Flux estimé |
| n_channels | int | Nombre de channels contributeurs |

---

### Table : `gold_amenagement_score`

**Description**  
Score final de pertinence des aménagements.

**Grain**  
1 ligne = 1 aménagement

**Colonnes**

| Colonne | Type | Description |
|------|------|------------|
| amenagement_id | string | Identifiant |
| score_pertinence | float | Score (0–100) |
| classe | string | Pertinent / Mitigé / Sous-utilisé |
| delta_pct | float | Variation relative |
| after_mean | float | Flux moyen après |
| confidence | string | Niveau de confiance |

---

## 🔹 EXPORTS LEAFLET

Les exports Leaflet sont dérivés des tables GOLD et SILVER.

- `leaflet_amenagements.geojson`
- `leaflet_sites.geojson`
- `leaflet_score.csv`

Aucune logique métier n’est implémentée côté Leaflet.
