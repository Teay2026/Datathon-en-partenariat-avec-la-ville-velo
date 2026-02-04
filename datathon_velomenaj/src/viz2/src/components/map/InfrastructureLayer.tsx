import { Polyline } from "react-leaflet";
import { Badge } from "@/components/ui/badge";
import { MapPopupCard } from "./MapPopupCard";
import type { InfraFeature, ScoreMap } from "@/lib/types";
import { multiLineStringToLatLng, getScoreColor } from "@/lib/types";

const DEFAULT_COLOR = "#6b7280"; // gray-500 for infrastructures without score

interface InfrastructurePolylineProps {
    feature: InfraFeature;
    scoreMap: ScoreMap;
}

function InfrastructurePolyline({
    feature,
    scoreMap,
}: InfrastructurePolylineProps) {
    const positions = multiLineStringToLatLng(feature.geometry.coordinates);

    // Get score from the map using feature id
    const score = scoreMap.get(feature.id);
    const color = score !== undefined ? getScoreColor(score) : DEFAULT_COLOR;

    const lengthText = `${feature.properties.longueur.toFixed(0)}m`;
    const networkText = feature.properties.reseau
        ? `${lengthText} • ${feature.properties.reseau}`
        : lengthText;

    return (
        <>
            {positions.map((linePositions, index) => (
                <Polyline
                    key={`${feature.id}-${index}-${score ?? "no-score"}`}
                    positions={linePositions}
                    color={color}
                    weight={3}
                    opacity={0.8}
                >
                    <MapPopupCard
                        title={feature.properties.nom}
                        description={feature.properties.commune1}
                    >
                        <div className="space-y-2">
                            <div className="flex flex-wrap gap-1">
                                <Badge variant="secondary">
                                    {feature.properties.typeamenagement}
                                </Badge>
                                {feature.properties.senscirculation && (
                                    <Badge variant="outline">
                                        {feature.properties.senscirculation}
                                    </Badge>
                                )}
                            </div>
                            <p className="text-xs text-muted-foreground">
                                {networkText}
                            </p>
                            {score !== undefined && (
                                <p className="text-xs font-medium">
                                    Score: {score.toFixed(2)}
                                </p>
                            )}
                            {feature.properties.anneelivraison && (
                                <p className="text-xs text-muted-foreground">
                                    Livraison:{" "}
                                    {feature.properties.anneelivraison}
                                </p>
                            )}
                        </div>
                    </MapPopupCard>
                </Polyline>
            ))}
        </>
    );
}

interface InfrastructureLayerProps {
    features: InfraFeature[];
    scoreMap: ScoreMap;
}

export function InfrastructureLayer({
    features,
    scoreMap,
}: InfrastructureLayerProps) {
    return (
        <>
            {features.map((feature) => (
                <InfrastructurePolyline
                    key={`${feature.id}-${scoreMap.size}`}
                    feature={feature}
                    scoreMap={scoreMap}
                />
            ))}
        </>
    );
}
