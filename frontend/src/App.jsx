import { useState, useEffect } from 'react';
import TabNavigation from './components/TabNavigation';
import FilterPanel from './components/FilterPanel';
import EAIStatusCard from './components/EAIStatusCard';
import { EAITrendChart, StatusDistributionChart, RegionComparisonChart } from './components/EAICharts';
import DataTable from './components/DataTable';
import CalculatorPage from './components/CalculatorPage';
import PredictionPage from './components/PredictionPage';
import { fetchRegions, fetchStations, fetchEAI } from './api';

function App() {
    const [activeTab, setActiveTab] = useState('statistics');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const [regions, setRegions] = useState([]);
    const [stations, setStations] = useState([]);
    const [eaiData, setEaiData] = useState(null);

    const [filters, setFilters] = useState({
        region: '',
        station: '',
        sample_type: '',
        water_layer: '',
        start_date: '',
        end_date: '',
    });

    // Load initial data
    useEffect(() => {
        loadInitialData();
    }, []);

    // Load stations when region changes
    useEffect(() => {
        loadStations();
    }, [filters.region]);

    const loadInitialData = async () => {
        try {
            setLoading(true);
            setError(null);

            const [regionsData, eaiResult] = await Promise.all([
                fetchRegions(),
                fetchEAI({ limit: 1000 }),
            ]);

            setRegions(regionsData.regions || []);
            setEaiData(eaiResult);
        } catch (err) {
            setError('Failed to load data. Make sure the API server is running on http://localhost:8000');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    const loadStations = async () => {
        try {
            const stationsData = await fetchStations(filters.region || null);
            setStations(stationsData.stations || []);
        } catch (err) {
            console.error('Failed to load stations:', err);
        }
    };

    const handleApplyFilters = async () => {
        try {
            setLoading(true);
            setError(null);

            const eaiResult = await fetchEAI({ ...filters, limit: 1000 });
            setEaiData(eaiResult);
        } catch (err) {
            setError('Failed to apply filters. Please try again.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    };

    // Render Statistics Page
    const renderStatisticsPage = () => (
        <>
            <FilterPanel
                filters={filters}
                setFilters={setFilters}
                onApply={handleApplyFilters}
                regions={regions}
                stations={stations}
            />

            {error && <div className="error">{error}</div>}

            {loading ? (
                <div className="loading">
                    <div className="spinner"></div>
                </div>
            ) : eaiData ? (
                <>
                    <EAIStatusCard
                        averageEAI={eaiData.average_eai}
                        statusDistribution={eaiData.status_distribution}
                    />

                    <div className="stats-grid">
                        <div className="stat-card good">
                            <h3>Good Status</h3>
                            <div className="stat-value">{eaiData.status_distribution.good || 0}</div>
                            <div className="stat-label">EAI ≥ 80</div>
                        </div>
                        <div className="stat-card warning">
                            <h3>Warning Status</h3>
                            <div className="stat-value">{eaiData.status_distribution.warning || 0}</div>
                            <div className="stat-label">EAI 50-79</div>
                        </div>
                        <div className="stat-card bad">
                            <h3>Bad Status</h3>
                            <div className="stat-value">{eaiData.status_distribution.bad || 0}</div>
                            <div className="stat-label">{"EAI < 50"}</div>
                        </div>
                        <div className="stat-card">
                            <h3>Total Samples</h3>
                            <div className="stat-value" style={{ color: '#3b82f6' }}>{eaiData.total}</div>
                            <div className="stat-label">In database</div>
                        </div>
                    </div>

                    <div className="charts-section">
                        <EAITrendChart data={eaiData.eai_scores} />
                        <StatusDistributionChart distribution={eaiData.status_distribution} />
                    </div>

                    <div style={{ marginBottom: '1.5rem' }}>
                        <RegionComparisonChart data={eaiData.eai_scores} />
                    </div>

                    <DataTable data={eaiData.eai_scores} />
                </>
            ) : (
                <div className="error">No data available</div>
            )}
        </>
    );

    // Render active tab content
    const renderContent = () => {
        switch (activeTab) {
            case 'statistics':
                return renderStatisticsPage();
            case 'calculator':
                return <CalculatorPage />;
            case 'prediction':
                return <PredictionPage regions={regions} />;
            default:
                return renderStatisticsPage();
        }
    };

    return (
        <div className="app">
            <header className="header">
                <h1>Environmental Alert Index</h1>
                <p>Marine Environment Monitoring Dashboard - Hong Kong Waters</p>
            </header>

            <TabNavigation activeTab={activeTab} setActiveTab={setActiveTab} />

            <main className="main-content">
                {renderContent()}
            </main>
        </div>
    );
}

export default App;
