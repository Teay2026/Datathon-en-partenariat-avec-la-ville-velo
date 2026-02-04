# 📊 Résumé du Module 2 : `spatial_usage`

## 🎯 Objectif

Lier les **compteurs vélo** aux **infrastructures cyclables** par proximité géographique et calculer les **flux journaliers** par aménagement.

---

## 📥 Entrées (Silver)

| Table | Description | Colonnes clés |
|-------|-------------|---------------|
| `silver_amenagements` | Infrastructures cyclables | `amenagement_id`, `centroid_lat`, `centroid_lon` |
| `silver_sites` | Emplacements des compteurs | `site_id`, `lat`, `lon` |
| `silver_channels` | Canaux de comptage | `channel_id`, `site_id`, `mode` |
| `silver_measures` | Mesures temporelles | `channel_id`, `date`, `flux`, `is_valid` |

---

## ⚙️ Traitements

```
┌─────────────────────────────────────────────────────────────────┐
│  1. JOINTURE SPATIALE                                           │
│     • Cross join amenagements × sites                           │
│     • Calcul distance Haversine (lat/lon → mètres)              │
│     • Filtre : distance ≤ 200m (buffer configurable)            │
│     Résultat : Paires (amenagement, site) proches               │
├─────────────────────────────────────────────────────────────────┤
│  2. FILTRAGE MODE VÉLO                                          │
│     • Join avec channels                                        │
│     • Filtre : mode == "velo"                                   │
│     Résultat : Liens amenagement ↔ channel vélo                 │
├─────────────────────────────────────────────────────────────────┤
│  3. AGRÉGATION JOURNALIÈRE                                      │
│     • Join avec measures (is_valid == True)                     │
│     • GroupBy (amenagement_id, date)                            │
│     • Sum(flux) → flux_estime                                   │
│     • CountDistinct(channel_id) → n_channels                    │
│     Résultat : Flux par aménagement par jour                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📤 Sorties (Gold)

| Table | Grain | Colonnes | Description |
|-------|-------|----------|-------------|
| `gold_link_amenagement_channel` | 1 lien = 1 amenagement × 1 channel | `amenagement_id`, `channel_id`, `site_id`, `distance_m` | Liens entre infrastructures et compteurs |
| `gold_flow_amenagement_daily` | 1 ligne = 1 amenagement × 1 jour | `amenagement_id`, `date`, `flux_estime`, `n_channels` | Flux journaliers agrégés |

---

## 🔧 Paramètres (config.yml)

| Paramètre | Valeur | Usage |
|-----------|--------|-------|
| `buffer_m` | 200 | Rayon de recherche (mètres) pour lier compteurs aux infrastructures |
| `bike_mode_value` | "velo" | Filtre pour ne garder que les canaux vélo |

---

## ✅ Contrôles Qualité

1. **Pas de doublons** dans les liens amenagement-channel
2. **Flux positifs** uniquement
3. **Au moins 1 channel** par jour/amenagement

---

## 📁 Structure des Fichiers Exportés

```
data/
├── silver/
│   ├── silver_amenagements.csv
│   ├── silver_sites.csv
│   ├── silver_channels.csv
│   └── silver_measures.csv
└── gold/
    ├── gold_link_amenagement_channel.csv
    └── gold_flow_amenagement_daily.csv
```

---

## 🔄 Flux de Données Simplifié

```
Amenagements ──┐
               ├──► Jointure Spatiale (200m) ──► Links ──┐
Sites ─────────┘                                         │
                                                         ├──► Flux Journaliers
Channels ──► Filtre vélo ────────────────────────────────┤
                                                         │
Measures ──► Filtre valides ─────────────────────────────┘
```

---

## 🎯 Interface avec Module 3 (Scoring)

Le Module 3 consommera :

- **`gold_flow_amenagement_daily`** → Pour calculer flux before/after ouverture
- **`silver_amenagements`** → Pour `annee_livraison` (date d'ouverture via règle midyear)

Et produira :
- `score_pertinence` (0-100)
- `delta_pct` (variation relative)
- `classe` (Pertinent / Mitigé / Sous-utilisé)
- `confidence` (niveau de confiance)

---

## 📝 Notes Techniques

### Formule Haversine (calcul de distance)

```python
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Rayon Terre en mètres
    φ1, φ2 = radians(lat1), radians(lat2)
    Δφ = radians(lat2 - lat1)
    Δλ = radians(lon2 - lon1)
    
    a = sin(Δφ/2)² + cos(φ1) * cos(φ2) * sin(Δλ/2)²
    c = 2 * atan2(√a, √(1-a))
    
    return R * c  # Distance en mètres
```

### Règle Midyear (Module 3)

Si `annee_livraison = 2020`, alors `date_ouverture = 2020-07-01`

---

## 🚀 Exécution

```bash
# Notebook interactif (développement)
jupyter notebook notebooks/02_spatial_usage_pandas.ipynb

# Pipeline production (quand disponible)
./scripts/run_usage.sh
```
