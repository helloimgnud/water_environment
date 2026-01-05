import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler,
} from 'chart.js';

ChartJS.register(
    CategoryScale,
    LinearScale,
    PointElement,
    LineElement,
    BarElement,
    ArcElement,
    Title,
    Tooltip,
    Legend,
    Filler
);

const chartColors = {
    good: '#22c55e',
    warning: '#eab308',
    bad: '#ef4444',
    unknown: '#6b7280',
    primary: '#3b82f6',
    secondary: '#8b5cf6',
};

// EAI Trend Line Chart
export function EAITrendChart({ data }) {
    if (!data || data.length === 0) {
        return <div className="chart-card"><p>No data available</p></div>;
    }

    // Sort by date and take last 50 points
    const sortedData = [...data]
        .filter(d => d.date && d.eai !== null)
        .sort((a, b) => new Date(a.date) - new Date(b.date))
        .slice(-50);

    const chartData = {
        labels: sortedData.map(d => d.date),
        datasets: [
            {
                label: 'EAI Score',
                data: sortedData.map(d => d.eai),
                borderColor: chartColors.primary,
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 6,
            },
            {
                label: 'Good Threshold (80)',
                data: sortedData.map(() => 80),
                borderColor: chartColors.good,
                borderDash: [5, 5],
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
            },
            {
                label: 'Warning Threshold (50)',
                data: sortedData.map(() => 50),
                borderColor: chartColors.warning,
                borderDash: [5, 5],
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'top',
                labels: { color: '#94a3b8' },
            },
        },
        scales: {
            x: {
                ticks: { color: '#94a3b8', maxRotation: 45 },
                grid: { color: 'rgba(71, 85, 105, 0.3)' },
            },
            y: {
                min: 0,
                max: 100,
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(71, 85, 105, 0.3)' },
            },
        },
    };

    return (
        <div className="chart-card">
            <h3> EAI Trend Over Time</h3>
            <div style={{ height: '300px' }}>
                <Line data={chartData} options={options} />
            </div>
        </div>
    );
}

// Status Distribution Doughnut Chart
export function StatusDistributionChart({ distribution }) {
    const chartData = {
        labels: ['Good (Tốt)', 'Warning (Cảnh cáo)', 'Bad (Xấu)', 'Unknown'],
        datasets: [
            {
                data: [
                    distribution.good || 0,
                    distribution.warning || 0,
                    distribution.bad || 0,
                    distribution.unknown || 0,
                ],
                backgroundColor: [
                    chartColors.good,
                    chartColors.warning,
                    chartColors.bad,
                    chartColors.unknown,
                ],
                borderColor: '#1e293b',
                borderWidth: 3,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: { color: '#94a3b8', padding: 15 },
            },
        },
    };

    return (
        <div className="chart-card">
            <h3> Status Distribution</h3>
            <div style={{ height: '300px' }}>
                <Doughnut data={chartData} options={options} />
            </div>
        </div>
    );
}

// Region/Station Comparison Bar Chart
export function RegionComparisonChart({ data }) {
    if (!data || data.length === 0) {
        return <div className="chart-card"><p>No data available</p></div>;
    }

    // Calculate average EAI per region
    const regionAvg = {};
    const regionCount = {};

    data.forEach(item => {
        if (item.region && item.eai !== null) {
            if (!regionAvg[item.region]) {
                regionAvg[item.region] = 0;
                regionCount[item.region] = 0;
            }
            regionAvg[item.region] += item.eai;
            regionCount[item.region]++;
        }
    });

    const regions = Object.keys(regionAvg);
    const averages = regions.map(r => (regionAvg[r] / regionCount[r]).toFixed(1));

    // Color based on EAI value
    const backgroundColors = averages.map(avg => {
        if (avg >= 80) return chartColors.good;
        if (avg >= 50) return chartColors.warning;
        return chartColors.bad;
    });

    const chartData = {
        labels: regions,
        datasets: [
            {
                label: 'Average EAI',
                data: averages,
                backgroundColor: backgroundColors,
                borderRadius: 6,
            },
        ],
    };

    const options = {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: 'y',
        plugins: {
            legend: { display: false },
        },
        scales: {
            x: {
                min: 0,
                max: 100,
                ticks: { color: '#94a3b8' },
                grid: { color: 'rgba(71, 85, 105, 0.3)' },
            },
            y: {
                ticks: { color: '#94a3b8' },
                grid: { display: false },
            },
        },
    };

    return (
        <div className="chart-card">
            <h3> EAI by Region</h3>
            <div style={{ height: '300px' }}>
                <Bar data={chartData} options={options} />
            </div>
        </div>
    );
}
