# 🚴 VéloMénaj : L'Intelligence Artificielle au service de la Mobilité

> **Optimiser le réseau cyclable de la Métropole de Lyon grâce à l'analyse de données et au Machine Learning.**

---

## 🎯 La Mission
Dans un contexte de transition écologique, le développement du vélo est une priorité. Mais où construire les prochaines pistes pour maximiser leur impact ?

**VéloMénaj** est une solution data-driven conçue pour accompagner les décideurs publics. Ce projet dépasse la simple visualisation pour offrir une **intelligence décisionnelle** : il qualifie l'efficacité du réseau actuel et recommande scientifiquement les futures zones d'implantation.

## 📊 Aperçu de la Solution
![Interface de Visualisation](dashboard_preview.png)
*Le dashboard interactif permettant d'explorer les flux, les scores de performance et les zones recommandées.*

---

## 🚀 Ce que le projet rend possible

### 1. Comprendre la Réalité (Analyse de Flux)
Nous agrégeons et nettoyons des données hétérogènes pour reconstruire une image fidèle des déplacements.
- **Visualisation Temporelle** : Analyse de l'évolution du trafic cycliste de 2014 à 2024.
- **Réconciliation Spatiale** : Croisement précis entre les compteurs physiques et la cartographie des aménagements.

### 2. Mesurer la Qualité (Scoring Intelligent)
Toutes les pistes ne se valent pas. Nous avons développé un algorithme de scoring composite :
- **Score d'Usage** : Basé sur le volume brut de cyclistes.
- **Score de Fiabilité** : Analyse la régularité du trafic (usage pendulaire vs loisir).
- **💡 Résultat** : Identification immédiate des axes structurants (« autoroutes à vélo ») et des discontinuités du réseau.

### 3. Prévoir l'Avenir (Machine Learning)
L'innovation majeure du projet réside dans son moteur de recommandation.
- **Modèle** : Utilisation d'algorithmes de **Forêts Aléatoires (Random Forest)**.
- **Méthode** : Simulation sur une grille géographique couvrant toute la métropole.
- **Impact** : Détection automatique des **zones à fort potentiel latent** (zones denses, mal desservies, propices au vélo) pour prioriser les investissements.

---

## 🛠️ Aperçu Technique
Ce projet démontre une maîtrise complète de la chaîne de valeur de la donnée, de l'ingestion brute à la restitution utilisateur.

| Domaine | Technologies Clés |
| :--- | :--- |
| **Big Data Processing** | **PySpark** & **Python** pour manipuler et nettoyer les grands jeux de données. |
| **Data Science & AI** | **Scikit-learn** pour les modèles prédictifs et **Pandas** pour l'analyse exploratoire. |
| **Intelligence Spatiale** | **Shapely** & **GeoJSON** pour les calculs géométriques et le mapping. |
| **Visualisation Web** | **Leaflet.js** (Cartographie) & **Chart.js** (Dataviz) pour une interface fluide sans backend lourd. |

---

## 📂 Structure du Projet
*   **`src/`** : Cœur du réacteur (Pipelines de nettoyage, calculs spatiaux, algo de scoring).
*   **`DataViz/`** : Interface web de restitution.
*   **`Nettoyage.ipynb` & `Prediction.ipynb`** : Notebooks de recherexhe et développement des modèles.

---
*Projet conçu pour allier excellence technique et impact sociétal concret sur la mobilité urbaine.*
