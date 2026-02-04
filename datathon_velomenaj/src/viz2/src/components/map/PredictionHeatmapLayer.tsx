import { Rectangle, Popup } from "react-leaflet";
import type { LatLngBoundsExpression } from "leaflet";
import predictionsData from "@/data/predictions_heatmap_lyon.json";

interface PredictionPoint {
    centroid_lat: number;
    centroid_lon: number;
    prob_success: number;
    recommendation: string;
}

const typedPredictionsData = predictionsData as PredictionPoint[];

// Grid cell size (approximate, based on data analysis)
const CELL_SIZE_LAT = 0.003; // ~330m
const CELL_SIZE_LON = 0.004; // ~300m

/**
 * Get color from probability (0 = red, 1 = green)
 */
function getProbabilityColor(prob: number): string {
    // Clamp probability between 0 and 1
    const p = Math.max(0, Math.min(1, prob));

    // Interpolate from red to yellow to green
    // prob 0 -> red (255, 0, 0)
    // prob 0.5 -> yellow (255, 255, 0)
    // prob 1 -> green (0, 255, 0)
    let r: number, g: number, b: number;

    if (p < 0.5) {
        // Red to yellow
        r = 255;
        g = Math.round(255 * (p * 2));
        b = 0;
    } else {
        // Yellow to green
        r = Math.round(255 * (1 - (p - 0.5) * 2));
        g = 255;
        b = 0;
    }

    return `rgb(${r}, ${g}, ${b})`;
}

interface PredictionCellProps {
    point: PredictionPoint;
}

function PredictionCell({ point }: PredictionCellProps) {
    const bounds: LatLngBoundsExpression = [
        [point.centroid_lat - CELL_SIZE_LAT / 2, point.centroid_lon - CELL_SIZE_LON / 2],
        [point.centroid_lat + CELL_SIZE_LAT / 2, point.centroid_lon + CELL_SIZE_LON / 2],
    ];

    const color = getProbabilityColor(point.prob_success);

    return (
        <Rectangle
            bounds={bounds}
            pathOptions={{
                color: color,
                fillColor: color,
                fillOpacity: 0.5,
                weight: 1,
                opacity: 0.7,
            }}
        >
            <Popup>
                <div className="flex flex-col gap-1">
                    <span className="font-semibold">Prédiction</span>
                    <span className="text-sm">
                        Probabilité de succès: {(point.prob_success * 100).toFixed(1)}%
                    </span>
                    <span className="text-sm text-muted-foreground">
                        {point.recommendation}
                    </span>
                </div>
            </Popup>
        </Rectangle>
    );
}

export function PredictionHeatmapLayer() {
    return (
        <>
            {typedPredictionsData.map((point, index) => (
                <PredictionCell key={`prediction-${index}`} point={point} />
            ))}
        </>
    );
}
