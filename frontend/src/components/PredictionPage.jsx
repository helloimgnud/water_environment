import { useState, useEffect } from 'react';
import { Line } from 'react-chartjs-2';
import api from '../api';

function PredictionPage({ regions }) {
    const [predictionTypes, setPredictionTypes] = useState([]);
    const [selectedType, setSelectedType] = useState('');
    const [areas, setAreas] = useState([]);
    const [selectedArea, setSelectedArea] = useState('');
    const [stations, setStations] = useState([]);
    const [selectedStation, setSelectedStation] = useState('');

    const [historicalData, setHistoricalData] = useState([]);
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [loadingHistory, setLoadingHistory] = useState(false);
    const [error, setError] = useState(null);
    const [filterApplied, setFilterApplied] = useState(false);

    // Fetch prediction types on mount
    useEffect(() => {
        api.get('/prediction/types')
            .then(res => setPredictionTypes(res.data.types || []))
            .catch(err => console.error('Error fetching types:', err));
    }, []);

    // Fetch areas when type changes
    useEffect(() => {
        if (!selectedType) {
            setAreas([]);
            setSelectedArea('');
            return;
        }
        api.get(`/prediction/areas?type_indicator=${selectedType}`)
            .then(res => {
                setAreas(res.data.areas || []);
                setSelectedArea('');
                setStations([]);
                setSelectedStation('');
                setFilterApplied(false);
                setHistoricalData([]);
                setPredictions([]);
            })
            .catch(err => console.error('Error fetching areas:', err));
    }, [selectedType]);

    // Fetch stations when area changes
    useEffect(() => {
        if (!selectedType || !selectedArea) {
            setStations([]);
            setSelectedStation('');
            return;
        }
        api.get(`/prediction/stations?type_indicator=${selectedType}&area=${encodeURIComponent(selectedArea)}`)
            .then(res => {
                setStations(res.data.stations || []);
                setSelectedStation('');
                setFilterApplied(false);
                setHistoricalData([]);
                setPredictions([]);
            })
            .catch(err => console.error('Error fetching stations:', err));
    }, [selectedType, selectedArea]);

    // Reset filter applied when station changes
    useEffect(() => {
        setFilterApplied(false);
        setHistoricalData([]);
        setPredictions([]);
    }, [selectedStation]);

    // Apply filter - fetch historical data
    const handleApplyFilter = async () => {
        if (!selectedType || !selectedArea || !selectedStation) return;

        setLoadingHistory(true);
        setError(null);
        setFilterApplied(false);
        setPredictions([]);

        // Determine sample type and water layer from selected type
        let sampleType = '';
        let waterLayer = '';
        if (selectedType === 'SEDIMENT') {
            sampleType = 'SEDIMENT';
        } else if (selectedType.startsWith('WATER_QUALITY')) {
            sampleType = 'WATER_QUALITY';
            if (selectedType.includes('SURFACE')) waterLayer = 'SURFACE';
            else if (selectedType.includes('MIDDLE')) waterLayer = 'MIDDLE';
            else if (selectedType.includes('BOTTOM')) waterLayer = 'BOTTOM';
        }

        let url = `/prediction/historical?region=${encodeURIComponent(selectedArea)}&station=${encodeURIComponent(selectedStation)}`;
        if (sampleType) url += `&sample_type=${sampleType}`;
        if (waterLayer) url += `&water_layer=${waterLayer}`;

        try {
            const res = await api.get(url);
            setHistoricalData(res.data.historical || []);
            setFilterApplied(true);
        } catch (err) {
            console.error('Error fetching historical:', err);
            setError('Failed to load historical data');
        } finally {
            setLoadingHistory(false);
        }
    };

    const handlePredict = async () => {
        if (!selectedType || !selectedArea || !selectedStation || !filterApplied) return;

        setLoading(true);
        setError(null);

        try {
            const response = await api.post('/prediction/forecast', {
                type_indicator: selectedType,
                area: selectedArea,
                station: selectedStation
            });

            setPredictions(response.data.predictions || []);
        } catch (err) {
            console.error('Error generating prediction:', err);
            setError(err.response?.data?.detail || err.message || 'Failed to generate prediction');
        } finally {
            setLoading(false);
        }
    };

    // Prepare chart data - connect predictions to last historical point
    const lastHistorical = historicalData.length > 0 ? historicalData[historicalData.length - 1] : null;

    // Add last historical point to predictions to create seamless connection
    const predictionDataWithConnection = lastHistorical && predictions.length > 0
        ? [{ x: lastHistorical.date, y: lastHistorical.eai }, ...predictions.map(d => ({ x: d.date, y: d.eai }))]
        : predictions.map(d => ({ x: d.date, y: d.eai }));

    const chartData = {
        labels: [
            ...historicalData.map(d => d.date),
            ...predictions.map(d => d.date)
        ],
        datasets: [
            {
                label: 'Historical EAI',
                data: historicalData.map(d => ({ x: d.date, y: d.eai })),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 3,
                pointBackgroundColor: '#3b82f6'
            },
            {
                label: 'Predicted EAI',
                data: predictionDataWithConnection,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.1)',
                borderDash: [5, 5],
                fill: true,
                tension: 0.3,
                pointRadius: predictions.length > 0 ? [0, ...predictions.map(() => 5)] : [],
                pointBackgroundColor: '#f59e0b',
                pointBorderColor: '#fff',
                pointBorderWidth: 2
            }
        ]
    };

    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8' }
            },
            tooltip: {
                callbacks: {
                    label: (ctx) => `EAI: ${ctx.parsed.y?.toFixed(1)}`
                }
            }
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8', maxTicksLimit: 12 },
                grid: { color: 'rgba(148, 163, 184, 0.1)' }
            },
            y: {
                min: 0,
                max: 100,
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(148, 163, 184, 0.1)' }
            }
        }
    };

    const getStatusClass = (status) => {
        if (status === 'good') return 'good';
        if (status === 'warning') return 'warning';
        if (status === 'bad') return 'bad';
        return '';
    };

    const canApply = selectedType && selectedArea && selectedStation;
    const canPredict = filterApplied && historicalData.length > 0;

    return (
        <div className="prediction-page">
            <div className="prediction-header">
                <h2>EAI Prediction</h2>
                <p>Predict future Environmental Alert Index based on Prophet time series models.</p>
            </div>

            {/* Prediction Controls */}
            <div className="prediction-controls">
                <div className="control-group">
                    <label>Sample Type</label>
                    <select
                        value={selectedType}
                        onChange={(e) => setSelectedType(e.target.value)}
                    >
                        <option value="">Choose type...</option>
                        {predictionTypes.map((t) => (
                            <option key={t.id} value={t.id}>{t.label}</option>
                        ))}
                    </select>
                </div>

                <div className="control-group">
                    <label>Area</label>
                    <select
                        value={selectedArea}
                        onChange={(e) => setSelectedArea(e.target.value)}
                        disabled={!selectedType}
                    >
                        <option value="">Choose area...</option>
                        {areas.map((a) => (
                            <option key={a} value={a}>{a}</option>
                        ))}
                    </select>
                </div>

                <div className="control-group">
                    <label>Station</label>
                    <select
                        value={selectedStation}
                        onChange={(e) => setSelectedStation(e.target.value)}
                        disabled={!selectedArea}
                    >
                        <option value="">Choose station...</option>
                        {stations.map((s) => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                </div>

                <button
                    className="btn btn-secondary"
                    onClick={handleApplyFilter}
                    disabled={!canApply || loadingHistory}
                >
                    {loadingHistory ? 'Loading...' : 'Apply Filter'}
                </button>

                <button
                    className="btn btn-primary"
                    onClick={handlePredict}
                    disabled={!canPredict || loading}
                    title={!canPredict ? 'Apply filter first to load historical data' : ''}
                >
                    {loading ? 'Predicting...' : 'Generate Prediction'}
                </button>
            </div>

            {/* Error Display */}
            {error && (
                <div className="error-message">{error}</div>
            )}

            {/* Chart Section */}
            {filterApplied && (historicalData.length > 0 || predictions.length > 0) && (
                <div className="prediction-chart-section">
                    <div className="chart-card">
                        <h3>
                            EAI Trend: {selectedStation} ({selectedArea})
                            {predictions.length > 0 && <span className="prediction-badge">+ 12 months forecast</span>}
                        </h3>
                        <div className="prediction-chart-container">
                            {loadingHistory ? (
                                <div className="loading"><div className="spinner"></div></div>
                            ) : (
                                <Line data={chartData} options={chartOptions} />
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Monthly Predictions Table */}
            {predictions.length > 0 && (
                <div className="prediction-results">
                    <div className="monthly-predictions">
                        <h3>12-Month Forecast</h3>
                        <div className="forecast-grid">
                            {predictions.map((p, idx) => (
                                <div key={idx} className={`forecast-card ${getStatusClass(p.status)}`}>
                                    <div className="forecast-month">{p.date}</div>
                                    <div className="forecast-eai">{p.eai?.toFixed(1) || 'N/A'}</div>
                                    <div className={`forecast-status ${p.status}`}>
                                        {p.status_label?.vi || p.status}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Legend */}
                    <div className="prediction-legend">
                        <div className="legend-item">
                            <span className="legend-color historical"></span>
                            <span>Historical Data (Recorded EAI)</span>
                        </div>
                        <div className="legend-item">
                            <span className="legend-color predicted"></span>
                            <span>Predicted Data (Forecasted EAI)</span>
                        </div>
                    </div>
                </div>
            )}

            {/* Empty State */}
            {!filterApplied && (
                <div className="empty-state">
                    <p>Select a sample type, area, and station, then click <strong>Apply Filter</strong> to view historical EAI data.</p>
                    <p style={{ marginTop: '0.5rem', fontSize: '0.9rem', opacity: 0.7 }}>
                        After viewing historical data, you can click <strong>Generate Prediction</strong> to forecast the next 12 months.
                    </p>
                </div>
            )}

            {filterApplied && historicalData.length === 0 && (
                <div className="empty-state">
                    <p>No historical data found for this selection. Try a different station or sample type.</p>
                </div>
            )}
        </div>
    );
}

export default PredictionPage;
