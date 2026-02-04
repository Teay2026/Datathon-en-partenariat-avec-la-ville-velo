import type { InfraTypeAmenagement } from "@/lib/types";

/**
 * Color mapping for different cycling infrastructure types
 */
export const infraColorMap: Record<InfraTypeAmenagement, string> = {
    "Piste Cyclable": "#22c55e", // green-500
    "Bande Cyclable": "#3b82f6", // blue-500
    "Voie verte": "#10b981", // emerald-500
    "Double sens cyclable": "#f59e0b", // amber-500
    "Couloir bus vélo non élargi": "#8b5cf6", // violet-500
    "Couloir bus vélo élargi": "#a855f7", // purple-500
    "Chaussée à voie centrale banalisée (CVCB)": "#ec4899", // pink-500
    "Goulotte ou rampe": "#6b7280", // gray-500
};

/**
 * Default color for unknown infrastructure types
 */
export const DEFAULT_INFRA_COLOR = "#6b7280"; // gray-500

/**
 * Get the color for an infrastructure type
 */
export function getInfraColor(typeamenagement: InfraTypeAmenagement): string {
    return infraColorMap[typeamenagement] ?? DEFAULT_INFRA_COLOR;
}
