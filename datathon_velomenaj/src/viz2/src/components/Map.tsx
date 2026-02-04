import { MapContainer, TileLayer } from "react-leaflet";
import countingLocations from "@/data/points_comptage.json";
import { InfrastructureLayer } from "@/components/map/InfrastructureLayer";
import { CountingLocationsLayer } from "@/components/map/CountingLocationsLayer";
import { PredictionHeatmapLayer } from "@/components/map/PredictionHeatmapLayer";
import type { InfraFeature, ComptageData, ScoreMap } from "@/lib/types";

const typedCountingLocations = countingLocations as unknown as ComptageData;

interface MapProps {
    filteredInfraFeatures: InfraFeature[];
    scoreMap: ScoreMap;
    selectedYear: number;
    showPredictionHeatmap: boolean;
}

export default function Map({
    filteredInfraFeatures,
    scoreMap,
    selectedYear,
    showPredictionHeatmap,
}: MapProps) {
    return (
        <MapContainer
            center={[45.7577778, 4.8322222]}
            zoom={14}
            className="h-full w-full rounded-md"
        >
            <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
            />

            {showPredictionHeatmap && <PredictionHeatmapLayer />}
            <InfrastructureLayer
                features={filteredInfraFeatures}
                scoreMap={scoreMap}
            />
            <CountingLocationsLayer
                features={typedCountingLocations.features}
                selectedYear={selectedYear}
            />
        </MapContainer>
    );
}
