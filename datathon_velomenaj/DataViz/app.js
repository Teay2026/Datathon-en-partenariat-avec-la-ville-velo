// Initialize Map centered on Lyon
const map = L.map('map').setView([45.75, 4.85], 13);

L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
    subdomains: 'abcd',
    maxZoom: 20
}).addTo(map);

// ========================
// UTILS
// ========================
function getSquareBounds(latlng, sideMeters) {
    const lat = latlng.lat;
    const lng = latlng.lng;

    // Earth radius approx 6378137 m
    // 1 deg lat ~= 111111 m
    // 1 deg lng ~= 111111 * cos(lat) m

    const halfSide = sideMeters / 2;

    const dLat = halfSide / 111111;
    const dLng = halfSide / (111111 * Math.cos(lat * Math.PI / 180));

    return [
        [lat - dLat, lng - dLng], // South-West
        [lat + dLat, lng + dLng]  // North-East
    ];
}

function getColorScore(s) {
    // Score is 0 to 1
    // Continuous Gradient: Red (Hue 0) to Green (Hue 120)
    // We map score (0-1) to Hue (0-120) directly.
    // 0 -> hsl(0, 100%, 50%) = Red
    // 0.5 -> hsl(60, 100%, 50%) = Yellow
    // 1 -> hsl(120, 100%, 50%) = Green

    // Clamp s between 0 and 1 just in case
    const score = Math.max(0, Math.min(1, s));
    const hue = score * 120;
    return `hsl(${hue}, 80%, 45%)`;
}

function getColorVolume(v) {
    // Volume: 100 to 5000+?
    return v > 200 ? '#800026' :
        v > 100 ? '#BD0026' :
            v > 50 ? '#E31A1C' :
                v > 20 ? '#FC4E2A' :
                    v > 10 ? '#FD8D3C' :
                        v > 10 ? '#FD8D3C' :
                            '#FEB24C';
}

function getColorProb(p) {
    // Probability is 0 to 1
    return p > 0.8 ? '#1a9850' : // Fast Green
        p > 0.6 ? '#91cf60' : // Light Green
            p > 0.4 ? '#fee08b' : // Yellow
                '#d73027';  // Red
}

// ========================
// LAYERS
// ========================
const layers = {};
let selectedYear = 'Global'; // Default
let amenitiesData = null; // Store data for re-styling

// 1. AMENITIES (Scored)
fetch('data/amenities.geojson')
    .then(r => r.json())
    .then(data => {
        amenitiesData = data;
        layers.amenities = L.geoJSON(data, {
            style: function (feature) {
                let s = feature.properties.score; // Default Global

                // If specific year selected
                if (selectedYear !== 'Global' && feature.properties.yearly_scores) {
                    s = feature.properties.yearly_scores[selectedYear];
                }

                // If no score for that year, gray out
                if (s === undefined || s === null) {
                    return { color: '#ccc', weight: 2, opacity: 0.5 };
                }

                return {
                    color: getColorScore(s),
                    weight: 4,
                    opacity: 0.8
                };
            },
            onEachFeature: function (feature, layer) {
                const p = feature.properties;
                let popupContent = `
                    <b>${p.nom || 'Aménagement'}</b><br>
                    Type: ${p.typeamenagement}<br>
                    Score Global: <b>${p.score ? p.score.toFixed(2) : 'N/A'}</b>
                `;

                if (selectedYear !== 'Global' && p.yearly_scores && p.yearly_scores[selectedYear] !== undefined) {
                    const yearlyScore = p.yearly_scores[selectedYear];
                    popupContent += `<br>Score ${selectedYear}: <b>${yearlyScore ? yearlyScore.toFixed(2) : 'N/A'}</b>`;
                }

                layer.bindPopup(popupContent);
            }
        }).addTo(map);

        updateControls();
    });

// 2. COUNTERS (Volume) - Circle Shape
fetch('data/counters.geojson')
    .then(r => r.json())
    .then(data => {
        layers.counters = L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                return L.circleMarker(latlng, {
                    radius: 6,
                    fillColor: getColorVolume(feature.properties.avg_volume),
                    color: "#fff",
                    weight: 1,
                    opacity: 1,
                    fillOpacity: 0.8
                });
            },
            onEachFeature: function (feature, layer) {
                const p = feature.properties;
                layer.bindPopup(`
                    <b>${p.site_name}</b><br>
                    Vol. Moyen: <b>${Math.round(p.avg_volume)}</b> /h
                `);
            }
        }).addTo(map);

        updateControls();
    });

// 3. PREDICTIONS - Star Shape (Colored)
fetch('data/predictions.geojson')
    .then(r => r.json())
    .then(data => {
        console.log("APP.JS: LOADING PREDICTIONS WITH GEOGRAPHIC SQUARES (v3)");
        layers.predictions = L.geoJSON(data, {
            pointToLayer: function (feature, latlng) {
                const color = getColorProb(feature.properties.prob_success);

                // User requested: square that COVERS a zone (scales with zoom).
                // Use L.rectangle which is a vector layer fixed to coordinates.
                // Assuming a zone size of approx 200m x 200m (standard grid).
                const bounds = getSquareBounds(latlng, 300); // 300m side

                return L.rectangle(bounds, {
                    color: "white",
                    weight: 1,
                    fillColor: color,
                    fillOpacity: 0.6
                });
            },
            onEachFeature: function (feature, layer) {
                const p = feature.properties;
                layer.bindPopup(`
                    <b>Zone Recommandée</b><br>
                    Probabilité: <b>${(p.prob_success * 100).toFixed(1)}%</b><br>
                    ${p.recommendation}
                `);
            }
        }).addTo(map); // Default ON

        updateControls();
    });

// 4. TENSION ZONES (Gap Analysis)
fetch('data/tension.geojson')
    .then(r => r.json())
    .then(data => {
        layers.tension = L.geoJSON(data, {
            style: {
                color: '#000000', // Black
                weight: 5,
                dashArray: '10, 10',
                opacity: 0.8
            },
            onEachFeature: function (feature, layer) {
                layer.bindPopup(`<b> Zone de Tension ⚠️</b><br>Amenagement: ${feature.properties.nom}<br>Volume Elevé + Score Faible`);
            }
        });
        // Do not addTo(map) by default to avoid clutter, or let user toggle. 
        // Let's add it but maybe user can toggle.
        // layers.tension.addTo(map); 

        updateControls();
    });


// 5. STATS LOGIC (Chart.js)
const btnStats = document.getElementById('btnStats');
const statsContainer = document.getElementById('statsContainer');
const btnCloseStats = document.getElementById('btnCloseStats');
let statsChart = null;

if (btnStats) {
    btnStats.addEventListener('click', () => {
        statsContainer.style.display = 'block';
        loadStats();
    });
}

if (btnCloseStats) {
    btnCloseStats.addEventListener('click', () => {
        statsContainer.style.display = 'none';
    });
}

function loadStats() {
    if (statsChart) return; // Already loaded

    fetch('data/stats.json')
        .then(r => r.json())
        .then(data => {
            // Data prep
            // Limit to top 15 types to avoid clutter
            const topData = data.slice(0, 15);

            const labels = topData.map(d => d.typeamenagement);
            const scores = topData.map(d => d.avg_score);
            const volumes = topData.map(d => d.avg_volume);

            const ctx = document.getElementById('statsChart').getContext('2d');

            statsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Score Moyen (Qualité)',
                            data: scores,
                            backgroundColor: '#1a9850',
                            yAxisID: 'y'
                        },
                        {
                            label: 'Volume Moyen (Usage)',
                            data: volumes,
                            backgroundColor: '#007bff',
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: { display: true, text: 'Score (0-1)' },
                            min: 0, max: 1
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: { display: true, text: 'Volume (vélos/h)' },
                            grid: {
                                drawOnChartArea: false, // only want the grid lines for one axis to show up
                            }
                        }
                    }
                }
            });
        });
}

// ========================
// CONTROLS & LEGEND
// ========================
let controlLayers = null;

function updateControls() {
    if (controlLayers) map.removeControl(controlLayers);

    // Only create if we have layers somewhat ready (or just simple check)
    if (layers.amenities && layers.counters && layers.predictions) {
        const overlays = {
            "Aménagements (Score)": layers.amenities,
            "Compteurs (Volume)": layers.counters,
            "Prédictions (Top Zones)": layers.predictions,
            "⚠️ Zones de Tension": layers.tension
        };
        controlLayers = L.control.layers(null, overlays, { collapsed: false }).addTo(map);
    }
}

// YEAR SLIDER LOGIC
const slider = document.getElementById('yearSlider');
const display = document.getElementById('yearDisplay');

if (slider) {
    // Initialize
    slider.value = 2024; // Default max? Or 'Global'?
    // Let's set 2025 as max if data allows. For now set to Global logic if we want.
    // User asked for year filter. Let's start with Global (maybe slider at max+1 or a checkbox).
    // The previous HTML edit set min=2014 max=2024.

    // Changing slider behavior: 
    // Let's say if user moves slider, we update.
    // Maybe add a checkbox for "Vue Globale"? 
    // Or just "2024" as default.
    selectedYear = slider.value;
    display.innerText = selectedYear;

    slider.addEventListener('input', (e) => {
        selectedYear = e.target.value;
        display.innerText = selectedYear;

        if (layers.amenities) {
            layers.amenities.setStyle(layers.amenities.options.style);
        }
    });
}

// LEGEND
const legend = L.control({ position: 'bottomright' });

legend.onAdd = function (map) {
    const div = L.DomUtil.create('div', 'legend');
    div.innerHTML += '<h4>Légende</h4>';

    // Score
    div.innerHTML += '<strong>Score Pertinence</strong><br>';
    div.innerHTML += '<i style="background: #1a9850; width: 18px; height: 3px; margin-top: 8px;"></i> Excellent (>0.8)<br>';
    div.innerHTML += '<i style="background: #fee08b; width: 18px; height: 3px; margin-top: 8px;"></i> Moyen (>0.2)<br>';
    div.innerHTML += '<i style="background: #d73027; width: 18px; height: 3px; margin-top: 8px;"></i> Faible<br><br>';

    // Volume
    div.innerHTML += '<strong>Compteurs (Volume)</strong><br>';
    div.innerHTML += '<i style="background: #800026; border-radius: 50%"></i> > 200 /h<br>';
    div.innerHTML += '<i style="background: #FC4E2A; border-radius: 50%"></i> > 20 /h<br>';

    // Pred
    div.innerHTML += '<br><strong>Prédictions (Proba)</strong><br>';
    // Legend needs to match the new square style (transparent colored squares)
    div.innerHTML += '<span style="display:inline-block; width:18px; height:18px; background:#1a9850; opacity:0.6; margin-right:5px; vertical-align:middle; border:1px solid #aaa;"></span> > 80%<br>';
    div.innerHTML += '<span style="display:inline-block; width:18px; height:18px; background:#fee08b; opacity:0.6; margin-right:5px; vertical-align:middle; border:1px solid #aaa;"></span> > 40%<br>';
    div.innerHTML += '<span style="display:inline-block; width:18px; height:18px; background:#d73027; opacity:0.6; margin-right:5px; vertical-align:middle; border:1px solid #aaa;"></span> Faible<br>';

    // Tension
    // Check if added already (failed previous attempt might have partially added or not)
    // The previous read showed it WAS added but duplicates might occur if I am not careful.
    // Actually the read showed lines 218-219 ALREADY HAVE Tension data.
    // So I should just make sure it's clean.
    // WAIT, line 213 in read file has duplicate line for > 40%.
    // I should fix that too.

    return div;
};

legend.addTo(map);
