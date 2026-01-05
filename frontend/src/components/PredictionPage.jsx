import { useState, useEffect } from 'react';

function PredictionPage({ regions }) {
    const [selectedRegion, setSelectedRegion] = useState('');
    const [predictionPeriod, setPredictionPeriod] = useState('30');
    const [loading, setLoading] = useState(false);
    const [prediction, setPrediction] = useState(null);

    const handlePredict = async () => {
        if (!selectedRegion) return;

        setLoading(true);
        // Placeholder - will be connected to prediction model later
        setTimeout(() => {
            setPrediction({
                region: selectedRegion,
                period: predictionPeriod,
                predicted_eai: (Math.random() * 40 + 50).toFixed(1),
                confidence: (Math.random() * 20 + 75).toFixed(1),
                trend: Math.random() > 0.5 ? 'improving' : 'declining',
                historical_avg: (Math.random() * 30 + 55).toFixed(1),
                predictions: Array.from({ length: 6 }, (_, i) => ({
                    month: `Month ${i + 1}`,
                    eai: (Math.random() * 40 + 50).toFixed(1),
                    status: Math.random() > 0.6 ? 'good' : Math.random() > 0.3 ? 'warning' : 'bad'
                }))
            });
            setLoading(false);
        }, 1500);
    };

    const getTrendIcon = (trend) => {
        return trend === 'improving' ? '' : '';
    };

    const getTrendClass = (trend) => {
        return trend === 'improving' ? 'improving' : 'declining';
    };

    return (
        <div className="prediction-page">
            <div className="prediction-header">
                <h2>EAI Prediction</h2>
                <p>Predict future Environmental Alert Index based on historical data and trends.</p>
                <div className="coming-soon-badge">Model Integration Coming Soon</div>
            </div>

            {/* Prediction Controls */}
            <div className="prediction-controls">
                <div className="control-group">
                    <label>Select Region</label>
                    <select
                        value={selectedRegion}
                        onChange={(e) => setSelectedRegion(e.target.value)}
                    >
                        <option value="">Choose a region...</option>
                        {regions.map((r) => (
                            <option key={r} value={r}>{r}</option>
                        ))}
                    </select>
                </div>

                <div className="control-group">
                    <label>Prediction Period</label>
                    <select
                        value={predictionPeriod}
                        onChange={(e) => setPredictionPeriod(e.target.value)}
                    >
                        <option value="30">Next 30 days</option>
                        <option value="90">Next 3 months</option>
                        <option value="180">Next 6 months</option>
                        <option value="365">Next 1 year</option>
                    </select>
                </div>

                <button
                    className="btn btn-primary"
                    onClick={handlePredict}
                    disabled={!selectedRegion || loading}
                >
                    {loading ? 'Predicting...' : 'Generate Prediction'}
                </button>
            </div>

            {/* Prediction Results */}
            {prediction && (
                <div className="prediction-results">
                    <div className="prediction-summary">
                        <div className="summary-card main-prediction">
                            <h3>Predicted EAI</h3>
                            <div className="prediction-value">{prediction.predicted_eai}</div>
                            <div className="prediction-region">{prediction.region}</div>
                        </div>

                        <div className="summary-card">
                            <h3>Confidence</h3>
                            <div className="confidence-value">{prediction.confidence}%</div>
                            <div className="confidence-bar">
                                <div
                                    className="confidence-fill"
                                    style={{ width: `${prediction.confidence}%` }}
                                />
                            </div>
                        </div>

                        <div className="summary-card">
                            <h3>Trend</h3>
                            <div className={`trend-indicator ${getTrendClass(prediction.trend)}`}>
                                <span className="trend-icon">{getTrendIcon(prediction.trend)}</span>
                                <span className="trend-text">{prediction.trend}</span>
                            </div>
                        </div>

                        <div className="summary-card">
                            <h3>Historical Avg</h3>
                            <div className="historical-value">{prediction.historical_avg}</div>
                            <div className="comparison">
                                {parseFloat(prediction.predicted_eai) > parseFloat(prediction.historical_avg)
                                    ? '+' + (prediction.predicted_eai - prediction.historical_avg).toFixed(1)
                                    : (prediction.predicted_eai - prediction.historical_avg).toFixed(1)
                                } from avg
                            </div>
                        </div>
                    </div>

                    {/* Monthly Predictions */}
                    <div className="monthly-predictions">
                        <h3>Monthly Forecast</h3>
                        <div className="forecast-grid">
                            {prediction.predictions.map((p, idx) => (
                                <div key={idx} className={`forecast-card ${p.status}`}>
                                    <div className="forecast-month">{p.month}</div>
                                    <div className="forecast-eai">{p.eai}</div>
                                    <div className={`forecast-status ${p.status}`}>{p.status}</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Placeholder Message */}
                    <div className="placeholder-message">
                        <p>
                            <strong>Note:</strong> This is a UI preview. The actual prediction model
                            will be integrated later using machine learning algorithms trained on
                            historical EAI data.
                        </p>
                    </div>
                </div>
            )}
        </div>
    );
}

export default PredictionPage;
