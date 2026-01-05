import { useState } from 'react';

// Parameter definitions for each sample type
const WATER_QUALITY_PARAMS = [
    { id: 'ph', label: 'pH', min: 0, max: 14, step: 0.1, unit: '' },
    { id: 'do_man', label: 'Salinity (do_man)', min: 0, max: 40, step: 0.1, unit: 'ppt' },
    { id: 'nhiet_do_nuoc', label: 'Water Temperature', min: 0, max: 40, step: 0.1, unit: '°C' },
    { id: 'nh3', label: 'Ammonia (NH3)', min: 0, max: 10, step: 0.01, unit: 'mg/L' },
    { id: 'tss', label: 'TSS', min: 0, max: 200, step: 1, unit: 'mg/L' },
    { id: 'bod5', label: 'BOD5', min: 0, max: 20, step: 0.1, unit: 'mg/L' },
];

const SEDIMENT_PARAMS = [
    { id: 'as', label: 'Arsenic (As)', min: 0, max: 50, step: 0.1, unit: 'mg/kg' },
    { id: 'cd', label: 'Cadmium (Cd)', min: 0, max: 5, step: 0.01, unit: 'mg/kg' },
    { id: 'pb', label: 'Lead (Pb)', min: 0, max: 100, step: 0.1, unit: 'mg/kg' },
    { id: 'cu', label: 'Copper (Cu)', min: 0, max: 150, step: 0.1, unit: 'mg/kg' },
    { id: 'zn', label: 'Zinc (Zn)', min: 0, max: 400, step: 1, unit: 'mg/kg' },
];

function CalculatorPage() {
    const [sampleType, setSampleType] = useState('WATER_QUALITY');
    const [inputValues, setInputValues] = useState({});
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [csvFile, setCsvFile] = useState(null);
    const [csvResults, setCsvResults] = useState(null);

    const params = sampleType === 'WATER_QUALITY' ? WATER_QUALITY_PARAMS : SEDIMENT_PARAMS;

    const handleInputChange = (paramId, value) => {
        setInputValues({ ...inputValues, [paramId]: value });
    };

    const handleSampleTypeChange = (type) => {
        setSampleType(type);
        setInputValues({});
        setResult(null);
    };

    const calculateEAI = async () => {
        setLoading(true);
        try {
            const response = await fetch('http://localhost:8000/calculate-eai', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    sample_type: sampleType,
                    data: inputValues
                })
            });
            const data = await response.json();
            setResult(data);
        } catch (error) {
            console.error('Error calculating EAI:', error);
            setResult({ error: 'Failed to calculate EAI. Make sure all required fields are filled.' });
        } finally {
            setLoading(false);
        }
    };

    const handleCsvUpload = (e) => {
        const file = e.target.files[0];
        if (file) {
            setCsvFile(file);
            setCsvResults(null);
        }
    };

    const processCsvFile = async () => {
        if (!csvFile) return;

        setLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', csvFile);
            formData.append('sample_type', sampleType);

            const response = await fetch('http://localhost:8000/calculate-eai-csv', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            setCsvResults(data);
        } catch (error) {
            console.error('Error processing CSV:', error);
            setCsvResults({ error: 'Failed to process CSV file.' });
        } finally {
            setLoading(false);
        }
    };

    const getStatusClass = (status) => {
        if (status === 'good') return 'good';
        if (status === 'warning') return 'warning';
        if (status === 'bad') return 'bad';
        return '';
    };

    return (
        <div className="calculator-page">
            <div className="calculator-header">
                <h2>EAI Calculator</h2>
                <p>Enter environmental parameters manually or upload a CSV file to calculate the Environmental Alert Index.</p>
            </div>

            {/* Sample Type Selection */}
            <div className="sample-type-selector">
                <button
                    className={`type-btn ${sampleType === 'WATER_QUALITY' ? 'active' : ''}`}
                    onClick={() => handleSampleTypeChange('WATER_QUALITY')}
                >
                    Water Quality
                </button>
                <button
                    className={`type-btn ${sampleType === 'SEDIMENT' ? 'active' : ''}`}
                    onClick={() => handleSampleTypeChange('SEDIMENT')}
                >
                    Sediment
                </button>
            </div>

            <div className="calculator-content">
                {/* Manual Input Section */}
                <div className="input-section">
                    <h3>Manual Input</h3>
                    <div className="param-grid">
                        {params.map((param) => (
                            <div key={param.id} className="param-input">
                                <label htmlFor={param.id}>
                                    {param.label}
                                    {param.unit && <span className="unit">({param.unit})</span>}
                                </label>
                                <input
                                    type="number"
                                    id={param.id}
                                    min={param.min}
                                    max={param.max}
                                    step={param.step}
                                    value={inputValues[param.id] || ''}
                                    onChange={(e) => handleInputChange(param.id, parseFloat(e.target.value))}
                                    placeholder={`${param.min} - ${param.max}`}
                                />
                            </div>
                        ))}
                    </div>
                    <button
                        className="btn btn-primary calculate-btn"
                        onClick={calculateEAI}
                        disabled={loading}
                    >
                        {loading ? 'Calculating...' : 'Calculate EAI'}
                    </button>

                    {/* Manual Input Result */}
                    {result && !result.error && (
                        <div className={`result-card ${getStatusClass(result.status)}`}>
                            <div className="result-eai">{result.eai?.toFixed(1) || 'N/A'}</div>
                            <div className="result-status">{result.status_label?.vi || result.status}</div>
                            <div className="result-details">
                                <h4>Sub-Indices:</h4>
                                <div className="sub-indices">
                                    {result.sub_indices && Object.entries(result.sub_indices).map(([key, value]) => (
                                        <div key={key} className="sub-index-item">
                                            <span className="sub-index-label">{key}:</span>
                                            <span className="sub-index-value">{value?.toFixed(1) || 'N/A'}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}
                    {result?.error && (
                        <div className="error-message">{result.error}</div>
                    )}
                </div>

                {/* CSV Upload Section */}
                <div className="csv-section">
                    <h3>CSV File Upload</h3>
                    <p className="csv-hint">
                        Upload a CSV file with columns matching the parameter names
                        ({sampleType === 'WATER_QUALITY' ? 'ph, do_man, nhiet_do_nuoc, nh3, tss, bod5' : 'as, cd, pb, cu, zn'})
                    </p>
                    <div className="csv-upload">
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleCsvUpload}
                            id="csv-input"
                        />
                        <label htmlFor="csv-input" className="csv-label">
                            {csvFile ? csvFile.name : 'Choose CSV file...'}
                        </label>
                        <button
                            className="btn btn-secondary"
                            onClick={processCsvFile}
                            disabled={!csvFile || loading}
                        >
                            Process CSV
                        </button>
                    </div>

                    {/* CSV Results */}
                    {csvResults && !csvResults.error && (
                        <div className="csv-results">
                            <h4>Results ({csvResults.results?.length || 0} records)</h4>
                            <div className="csv-summary">
                                <div className="summary-item good">Good: {csvResults.summary?.good || 0}</div>
                                <div className="summary-item warning">Warning: {csvResults.summary?.warning || 0}</div>
                                <div className="summary-item bad">Bad: {csvResults.summary?.bad || 0}</div>
                            </div>
                            <div className="csv-table-container">
                                <table className="data-table">
                                    <thead>
                                        <tr>
                                            <th>#</th>
                                            <th>EAI</th>
                                            <th>Status</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {csvResults.results?.slice(0, 20).map((row, idx) => (
                                            <tr key={idx}>
                                                <td>{idx + 1}</td>
                                                <td>{row.eai?.toFixed(1) || 'N/A'}</td>
                                                <td>
                                                    <span className={`status-badge ${row.status}`}>
                                                        {row.status_label?.vi || row.status}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    )}
                    {csvResults?.error && (
                        <div className="error-message">{csvResults.error}</div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default CalculatorPage;
