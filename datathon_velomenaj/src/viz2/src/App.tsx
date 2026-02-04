import { useState, useMemo, useEffect } from "react";
import Map from "./components/Map";
import { Card, CardHeader, CardTitle, CardContent } from "./components/ui/card";
import { Slider } from "@/components/ui/slider";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import infraData from "@/data/infra.json";
import type { InfraData, ScoreEntry, ScoreMap } from "@/lib/types";
import { createScoreMap } from "@/lib/types";
import "leaflet/dist/leaflet.css";

const typedInfraData = infraData as unknown as InfraData;

// Get min and max years from the data
const years = typedInfraData.features
    .map((f) => f.properties.anneelivraison)
    .filter((y): y is number => y !== null);
const minYear = 2014;
const maxYear = Math.max(...years);

// Fetch score data using fetch API
async function loadScoreData(year: number): Promise<ScoreMap> {
    try {
        const response = await fetch(`/src/data/${year}.json`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const entries: ScoreEntry[] = await response.json();
        const scoreMap = createScoreMap(entries);
        return scoreMap;
    } catch (error) {
        return new globalThis.Map<string, number>();
    }
}

export function App() {
    const [selectedYear, setSelectedYear] = useState<number>(maxYear);
    const [scoreMap, setScoreMap] = useState<ScoreMap>(
        () => new globalThis.Map(),
    );
    const [loadingScores, setLoadingScores] = useState<boolean>(true);
    const [showPredictionHeatmap, setShowPredictionHeatmap] =
        useState<boolean>(false);

    // Load score data when year changes
    useEffect(() => {
        let cancelled = false;
        setLoadingScores(true);
        loadScoreData(selectedYear).then((data) => {
            if (!cancelled) {
                setScoreMap(data);
                setLoadingScores(false);
            }
        });
        return () => {
            cancelled = true;
        };
    }, [selectedYear]);

    const filteredFeatures = useMemo(() => {
        return typedInfraData.features.filter((feature) => {
            const year = feature.properties.anneelivraison;
            // Include features with no year or year <= selected year
            return year === null || year <= selectedYear;
        });
    }, [selectedYear]);

    return (
        <div className="bg-background w-full h-screen flex flex-col p-6 gap-4">
            <header>
                <h1 className="text-2xl font-semibold tracking-tight">
                    Velo'Menaj
                </h1>
            </header>
            <div className="flex-1 flex flex-col lg:flex-row gap-4 min-h-0">
                <Card className="flex-1 lg:flex-3 p-4 min-h-75 lg:min-h-0 ">
                    <div className="h-full w-full">
                        <Map
                            filteredInfraFeatures={filteredFeatures}
                            scoreMap={scoreMap}
                            selectedYear={selectedYear}
                            showPredictionHeatmap={showPredictionHeatmap}
                        />
                    </div>
                </Card>

                <div className="flex-1 flex flex-col gap-4">
                    <Card>
                        <CardHeader>
                            <CardTitle>Contrôles</CardTitle>
                        </CardHeader>
                        <CardContent className="flex flex-col gap-4">
                            <div className="flex flex-col gap-2">
                                <label className="text-sm font-medium">
                                    Année de livraison
                                </label>
                                <div className="flex items-center gap-4">
                                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                                        {minYear}
                                    </span>
                                    <Slider
                                        value={[selectedYear]}
                                        min={minYear}
                                        max={maxYear}
                                        step={1}
                                        onValueChange={(value) =>
                                            setSelectedYear(value[0])
                                        }
                                        className="flex-1"
                                    />
                                    <span className="text-sm text-muted-foreground whitespace-nowrap">
                                        {maxYear}
                                    </span>
                                </div>
                                <span className="text-sm font-medium text-center">
                                    Jusqu'à {selectedYear}
                                    {loadingScores && " (chargement...)"}
                                </span>
                            </div>
                            <div className="flex items-center gap-2">
                                <Checkbox
                                    id="prediction-heatmap"
                                    checked={showPredictionHeatmap}
                                    onCheckedChange={(checked) =>
                                        setShowPredictionHeatmap(
                                            checked === true,
                                        )
                                    }
                                />
                                <Label
                                    htmlFor="prediction-heatmap"
                                    className="text-sm font-medium cursor-pointer"
                                >
                                    Afficher la heatmap de prédiction
                                </Label>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <CardTitle>Légende</CardTitle>
                        </CardHeader>
                        <CardContent>
                            <div className="flex flex-col gap-1">
                                <span className="text-sm text-muted-foreground">
                                    Score:
                                </span>
                                <div
                                    className="h-4 rounded w-full"
                                    style={{
                                        background:
                                            "linear-gradient(to right, rgb(239, 68, 68), rgb(34, 197, 94))",
                                    }}
                                />
                                <div className="flex justify-between text-xs text-muted-foreground">
                                    <span>0</span>
                                    <span>1</span>
                                </div>
                            </div>
                        </CardContent>
                    </Card>
                    <Card>
                        <CardHeader>
                            <CardTitle>Informations</CardTitle>
                        </CardHeader>
                        <CardContent className="text-sm text-muted-foreground">
                            <p>
                                Cette application visualise les aménagements
                                cyclables dans la Métropole de Lyon. Utilisez le
                                curseur pour filtrer les aménagements par année
                                de livraison. Les couleurs représentent le score
                                de chaque infrastructure (rouge = 0, vert = 1).
                                Le score représente le nombre de passage devant
                                les bornes de comptage, et l'utilisation des
                                aménagements cyclables.
                            </p>
                        </CardContent>
                    </Card>
                </div>
            </div>
        </div>
    );
}

export default App;
