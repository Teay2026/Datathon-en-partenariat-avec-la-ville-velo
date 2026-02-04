import L from "leaflet";
import { useMemo } from "react";
import { Marker } from "react-leaflet";
import { Badge } from "@/components/ui/badge";
import { MapPopupCard } from "./MapPopupCard";
import type { ComptageFeature, LatLngTuple } from "@/lib/types";
import veloParAnnee from "@/data/velo_par_annee.json";

type VeloParAnneeData = Record<string, Record<string, number>>;

const typedVeloParAnnee = veloParAnnee as VeloParAnneeData;

const getHueFromData = (value: number, max: number) => {
    // 0 -> 140 (red), value == max -> 240 (green)
    return 140 + (100 * value) / max;
};

const createDynamicIcon = (hue: number) => {
    return L.divIcon({
        className: "custom-dynamic-marker",
        html: `
            <div style="filter: hue-rotate(${hue}deg); width: 25px; height: 41px;">
                <img src="https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png"
                     style="width: 25px; height: 41px;" />
            </div>
        `,
        iconSize: [25, 41],
        iconAnchor: [12, 41],
        popupAnchor: [1, -34],
    });
};

interface CountingLocationMarkerProps {
    feature: ComptageFeature;
    score: number;
    veloCount: number;
}

function CountingLocationMarker({
    feature,
    score,
    veloCount,
}: CountingLocationMarkerProps) {
    const position: LatLngTuple = [
        feature.geometry.coordinates[1],
        feature.geometry.coordinates[0],
    ];

    const hue = getHueFromData(score, 1);

    return (
        <Marker position={position} icon={createDynamicIcon(hue)}>
            <MapPopupCard
                title={feature.properties.site_name}
                description={`Site ID: ${feature.properties.site_id}`}
            >
                <div className="flex flex-col gap-1">
                    {feature.properties.infrastructure_type && (
                        <Badge variant="secondary">
                            {feature.properties.infrastructure_type}
                        </Badge>
                    )}
                    <span className="text-sm text-muted-foreground">
                        Passages: {veloCount.toLocaleString()}
                    </span>
                </div>
            </MapPopupCard>
        </Marker>
    );
}

interface CountingLocationsLayerProps {
    features: ComptageFeature[];
    selectedYear: number;
}

export function CountingLocationsLayer({
    features,
    selectedYear,
}: CountingLocationsLayerProps) {
    // Get the data for the selected year
    const yearData = useMemo(() => {
        const yearKey = String(selectedYear);
        return typedVeloParAnnee[yearKey] || {};
    }, [selectedYear]);

    // Calculate the average for the year
    const yearAverage = useMemo(() => {
        const values = Object.values(yearData);
        if (values.length === 0) return 0;
        const sum = values.reduce((acc, val) => acc + val, 0);
        return sum / values.length;
    }, [yearData]);

    // Filter features that have data for the selected year and calculate scores
    const featuresWithData = useMemo(() => {
        // Calculate score for each feature based on velo count vs average
        // Score = 0 if less than 50% of average
        // Score varies from 0 to 1 for 50% to 150% of average
        const calculateScore = (veloCount: number): number => {
            if (yearAverage === 0) return 0;

            const ratio = veloCount / yearAverage;

            // If less than 50% of average, score = 0
            if (ratio < 0.5) return 0;

            // If more than 150% of average, score = 1
            if (ratio >= 1.5) return 1;

            // Linear interpolation between 50% and 150%
            // At 50% (ratio = 0.5) -> score = 0
            // At 150% (ratio = 1.5) -> score = 1
            return (ratio - 0.5) / 1.0;
        };

        return features
            .map((feature) => {
                const siteId = feature.properties.site_id;
                const veloCount = yearData[siteId];

                if (veloCount === undefined) {
                    return null;
                }

                return {
                    feature,
                    veloCount,
                    score: calculateScore(veloCount),
                };
            })
            .filter(
                (
                    item,
                ): item is {
                    feature: ComptageFeature;
                    veloCount: number;
                    score: number;
                } => item !== null,
            );
    }, [features, yearData, yearAverage]);

    return (
        <>
            {featuresWithData.map(({ feature, veloCount, score }) => (
                <CountingLocationMarker
                    key={feature.id}
                    feature={feature}
                    score={score}
                    veloCount={veloCount}
                />
            ))}
        </>
    );
}
