# 📘 Guide des Notebooks Clés

Ce document référence les notebooks essentiels pour comprendre et exécuter le pipeline de données.

## 1. Nettoyage (`Nettoyage.ipynb`)
**Objectif :** Préparer les données pour l'analyse.
- Ingestion des fichiers bruts (Bronze).
- Nettoyage, typage et standardisation.
- Export vers la couche **Silver**.

## 2. Analyse Spatiale (`src/spatial_usage/04_spatial_usage_direct_measures.ipynb`)
**Objectif :** Calculer les flux de vélos sur les aménagements.
- Association spatiale entre les compteurs vélo et les aménagements cyclables.
- Calcul des volumes de trafic quotidiens.
- Export vers la couche **Gold** (`gold_flow_amenagement_daily`).

## 3. Scoring (`Scoring2.ipynb`)
**Objectif :** Évaluer la performance des aménagements.
- Calcul du **Score d'Usage** (basé sur le volume).
- Calcul du **Score de Stabilité** (basé sur la régularité).
- Génération du score global (pondéré).
- Export vers `amenagement_scoring_global_json_2`.

## 4. Prédiction (`Prediction_2.ipynb`)
**Objectif :** Recommander les futures zones d'implantation.
- Entraînement d'un modèle **Random Forest**.
- Simulation sur une grille géographique (Métropole de Lyon).
- Identification des 50 zones les plus propices (Top 10% potentiel).
- Export vers `predictions_heatmap_lyon_2.json`.
