import numpy as np
import pandas as pd
import logging
import time

# =========================
# LOGGING SETUP
# =========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger(__name__)

# =========================
# 0) LIRE ids.txt (1 id / ligne)
# =========================
IDS_PATH = "ids.txt"
logger.info("Lecture des IDs depuis %s", IDS_PATH)

with open(IDS_PATH, "r", encoding="utf-8") as f:
    amenagements_ids = [line.strip() for line in f if line.strip()]

# Supprimer doublons en gardant l'ordre
seen = set()
amenagements_ids = [x for x in amenagements_ids if not (x in seen or seen.add(x))]

if not amenagements_ids:
    logger.error("ids.txt est vide")
    raise ValueError("ids.txt est vide")

logger.info("Nombre d'aménagements chargés : %d", len(amenagements_ids))

# =========================
# PARAMÈTRES GLOBAUX
# =========================
START_DATE = "2014-01-01"
END_DATE = "2025-12-01"
SEED = 42

np.random.seed(SEED)

dates_full = pd.date_range(start=START_DATE, end=END_DATE, freq="D")
dates_recent = pd.date_range(start="2025-06-01", end=END_DATE, freq="D")

logger.info("Période globale : %s → %s", START_DATE, END_DATE)
logger.info("Jours (full): %d | Jours (recent): %d", len(dates_full), len(dates_recent))

# =========================
# PROFILS D'USAGE
# =========================
PROFILES = {
    "high_stable": {"base_flux": (300, 600), "trend": 0.0, "noise": 0.15},
    "medium_growing": {"base_flux": (80, 200), "trend": 0.002, "noise": 0.25},
    "high_declining": {"base_flux": (250, 500), "trend": -0.002, "noise": 0.20},
    "low_stable": {"base_flux": (10, 40), "trend": 0.0, "noise": 0.30},
    "erratic": {"base_flux": (20, 150), "trend": 0.0, "noise": 0.60},
}

profile_names = list(PROFILES.keys())
profile_probs = [0.2, 0.25, 0.15, 0.25, 0.15]

# =========================
# GÉNÉRATION DES DONNÉES
# =========================
rows = []
start_time = time.time()

log_every = max(1, len(amenagements_ids) // 10)  # log tous les 10 %

for idx, amenagement_id in enumerate(amenagements_ids, start=1):
    is_recent = amenagement_id.startswith("AMEN_RECENT")

    if is_recent:
        dates = dates_recent
        base_flux = np.random.uniform(50, 150)
        trend = 0.0
        noise_level = 0.35
    else:
        dates = dates_full
        profile = np.random.choice(profile_names, p=profile_probs)
        cfg = PROFILES[profile]

        base_flux = np.random.uniform(*cfg["base_flux"])
        trend = cfg["trend"]
        noise_level = cfg["noise"]

    n_channels = np.random.randint(1, 5)

    for t, date in enumerate(dates):
        trend_factor = 1 + trend * t
        seasonal = 1 + 0.30 * np.sin(2 * np.pi * t / 365)
        noise = np.random.normal(0, noise_level)

        flux = base_flux * trend_factor * seasonal * (1 + noise)
        flux = max(0, flux)

        rows.append(
            {
                "amenagement_id": amenagement_id,
                "date": date.date(),
                "flux_estime": int(round(flux)),
                "n_channels": n_channels,
            }
        )

    if idx % log_every == 0 or idx == len(amenagements_ids):
        elapsed = time.time() - start_time
        logger.info(
            "Progression: %d / %d aménagements (%.1f%%) | lignes générées: %d | %.1fs écoulées",
            idx,
            len(amenagements_ids),
            100 * idx / len(amenagements_ids),
            len(rows),
            elapsed,
        )

# =========================
# DATAFRAME FINAL
# =========================
logger.info("Construction du DataFrame pandas")
df = pd.DataFrame(rows)

# =========================
# CONTRÔLES DE COHÉRENCE
# =========================
logger.info("Vérification de cohérence des IDs")

generated_ids = set(df["amenagement_id"].unique())
expected_ids = set(amenagements_ids)

assert generated_ids == expected_ids, (
    "❌ Incohérence IDs.\n"
    f"Manquants: {sorted(expected_ids - generated_ids)[:10]}\n"
    f"En trop: {sorted(generated_ids - expected_ids)[:10]}"
)

logger.info("Cohérence des IDs OK")

# =========================
# SORTIE
# =========================
output_csv = "gold_flow_amenagement_daily_mock.csv"
logger.info("Écriture du fichier CSV : %s", output_csv)

df.to_csv(output_csv, index=False)

logger.info("✅ Génération terminée avec succès")
logger.info("Lignes totales : %d", len(df))
logger.info("Aménagements : %d", df["amenagement_id"].nunique())
logger.info("Période : %s → %s", df["date"].min(), df["date"].max())
