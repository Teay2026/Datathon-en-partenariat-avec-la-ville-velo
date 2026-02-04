/**
 * TypeScript Types for GeoJSON Data
 *
 * These types are generated based on actual analysis of the JSON data files.
 * Run `npx tsx src/lib/analyzeData.ts` to re-analyze the data.
 */

// ============================================================
// Infrastructure Types (infra.json)
// ============================================================

/**
 * Type d'aménagement cyclable (primary)
 */
export type InfraTypeAmenagement =
    | "Piste Cyclable"
    | "Bande Cyclable"
    | "Voie verte"
    | "Couloir bus vélo non élargi"
    | "Couloir bus vélo élargi"
    | "Chaussée à voie centrale banalisée (CVCB)"
    | "Double sens cyclable"
    | "Goulotte ou rampe";

/**
 * Type d'aménagement cyclable (secondary, can be null)
 */
export type InfraTypeAmenagement2 =
    | "Double sens cyclable"
    | "Couloir bus vélo non élargi"
    | "Bande Cyclable"
    | "Couloir bus vélo élargi"
    | "Piste Cyclable"
    | "Voie verte"
    | "Chaussée à voie centrale banalisée (CVCB)"
    | null;

/**
 * Réseau cyclable
 */
export type InfraReseau =
    | "Réseau secondaire"
    | "Réseau de desserte"
    | "Réseau structurant et super structurant"
    | null;

/**
 * Positionnement de l'aménagement
 */
export type InfraPositionnement =
    | "Unilatérale bidirectionnelle"
    | "Unilatérale unidirectionnelle"
    | "Bilatérale unidirectionnelle"
    | "Sans objet"
    | "Bilatérale bidirectionnelle";

/**
 * Sens de circulation
 */
export type InfraSensCirculation =
    | "Double"
    | "Sens Unique"
    | "Sans Objet"
    | null;

/**
 * Environnement de l'aménagement
 */
export type InfraEnvironnement =
    | "Voie de circulation"
    | "Tunnel - Passerelle"
    | "Sans objet"
    | "Parc"
    | "Berges - Chemin de halage"
    | null;

/**
 * Localisation de l'aménagement
 */
export type InfraLocalisation =
    | "Sur trottoir"
    | "Sur chaussée"
    | "Sans objet"
    | null;

/**
 * Typologie de piste
 */
export type InfraTypologiePiste =
    | "Piste sur trottoir"
    | "Piste sur chaussée"
    | "Piste intercalée entre trottoir et stationnement"
    | "Autre"
    | "Piste sur chaussée à hauteur intermédiaire"
    | null;

/**
 * Domanialité (ownership)
 */
export type InfraDomanialite =
    | "Métropole"
    | "Métropole (ex-RD)"
    | "Privé"
    | "État"
    | "Commune"
    | "Métropole entretien CG";

/**
 * Réglementation
 */
export type InfraReglementation =
    | "Vélo facultatif"
    | "Vélo obligatoire"
    | "Contresens (sens réservé)"
    | "Voie verte"
    | "Sans objet"
    | "Zone 30"
    | "Aire piétonne"
    | "Zone de rencontre"
    | "Autre"
    | null;

/**
 * Zone de circulation apaisée
 */
export type InfraZoneCirculationApaisee =
    | "Zone de rencontre"
    | "Zone 30"
    | "Aire Piétonne"
    | null;

/**
 * Validité
 */
export type InfraValidite = "Validé" | "En projet ou en cours de validation";

/**
 * Infrastructure feature properties
 */
export interface InfraProperties {
    nom: string;
    commune1: string;
    insee1: string;
    commune2: string | null;
    insee2: string | null;
    reseau: InfraReseau;
    financementac: string;
    typeamenagement: InfraTypeAmenagement;
    typeamenagement2: InfraTypeAmenagement2;
    positionnement: InfraPositionnement;
    senscirculation: InfraSensCirculation;
    environnement: InfraEnvironnement;
    localisation: InfraLocalisation;
    typologiepiste: InfraTypologiePiste;
    revetementpiste: string | null;
    domanialite: InfraDomanialite;
    reglementation: InfraReglementation;
    zonecirculationapaisee: InfraZoneCirculationApaisee;
    anneelivraison: number | null;
    longueur: number;
    observation: string | null;
    validite: InfraValidite;
    gid: number;
}

/**
 * Infrastructure geometry (MultiLineString)
 */
export interface InfraGeometry {
    type: "MultiLineString";
    coordinates: number[][][];
}

/**
 * Infrastructure feature
 */
export interface InfraFeature {
    type: "Feature";
    id: string;
    geometry: InfraGeometry;
    geometry_name: string;
    properties: InfraProperties;
    bbox: number[];
}

/**
 * Infrastructure FeatureCollection
 */
export interface InfraData {
    type: "FeatureCollection";
    features: InfraFeature[];
}

// ============================================================
// Counting Locations Types (points_comptage.json)
// ============================================================

/**
 * Type d'infrastructure de comptage
 */
export type ComptageInfrastructureType = "" | "OTHER SPECIFIC SITE";

/**
 * Counting location properties
 */
export interface ComptageProperties {
    gid: string;
    site_id: string;
    parent_site_id: string;
    fr_insee_code: string;
    xlong: number;
    ylat: number;
    external_ids: string;
    infrastructure_type: ComptageInfrastructureType;
    site_name: string;
}

/**
 * Counting location geometry (Point)
 */
export interface ComptageGeometry {
    type: "Point";
    coordinates: [number, number];
}

/**
 * Counting location feature
 */
export interface ComptageFeature {
    type: "Feature";
    id: string;
    geometry: ComptageGeometry;
    geometry_name: string;
    properties: ComptageProperties;
    bbox: number[];
}

/**
 * Counting locations FeatureCollection
 */
export interface ComptageData {
    type: "FeatureCollection";
    features: ComptageFeature[];
}

// ============================================================
// Utility Types
// ============================================================

/**
 * LatLng tuple for Leaflet
 */
export type LatLngTuple = [number, number];

/**
 * Convert GeoJSON coordinates [lng, lat] to Leaflet [lat, lng]
 */
export function toLatLng(coordinates: [number, number]): LatLngTuple {
    return [coordinates[1], coordinates[0]];
}

/**
 * Convert MultiLineString coordinates to Leaflet positions
 */
export function multiLineStringToLatLng(
    coordinates: number[][][],
): LatLngTuple[][] {
    return coordinates.map((lineString) =>
        lineString.map((coord) => [coord[1], coord[0]] as LatLngTuple),
    );
}

// ============================================================
// Score Data Types (yearly score files)
// ============================================================

/**
 * Score entry for an infrastructure
 */
export interface ScoreEntry {
    amenagement_id: string;
    score: number;
}

/**
 * Map of amenagement_id to score for quick lookup
 */
export type ScoreMap = globalThis.Map<string, number>;

/**
 * Convert score entries array to a lookup map
 */
export function createScoreMap(entries: ScoreEntry[]): ScoreMap {
    return new Map(entries.map((entry) => [entry.amenagement_id, entry.score]));
}

/**
 * Get color from score (0 = red, 1 = green)
 */
export function getScoreColor(score: number): string {
    // Clamp score between 0 and 1
    const s = Math.max(0, Math.min(1, score));

    // Interpolate from red (#ef4444) to green (#22c55e)
    // Red: rgb(239, 68, 68)
    // Green: rgb(34, 197, 94)
    const r = Math.round(239 + (34 - 239) * s);
    const g = Math.round(68 + (197 - 68) * s);
    const b = Math.round(68 + (94 - 68) * s);

    return `rgb(${r}, ${g}, ${b})`;
}

// ============================================================
// Prediction Heatmap Types (predictions_heatmap_lyon.json)
// ============================================================

/**
 * Prediction heatmap entry
 */
export interface PredictionHeatmapEntry {
    centroid_lat: number;
    centroid_lon: number;
    prob_success: number;
    recommendation: string;
}
