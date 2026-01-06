import { useState } from 'react';
import api from '../api';

// All parameter definitions - shown together
const ALL_PARAMS = {
    waterQuality: [
        { id: 'ph', label: 'pH', min: 0, max: 14, step: 0.1, unit: '' },
        { id: 'do_man', label: 'Salinity', min: 0, max: 40, step: 0.1, unit: 'ppt' },
        { id: 'nhiet_do_nuoc', label: 'Water Temp', min: 0, max: 40, step: 0.1, unit: '°C' },
        { id: 'nh3', label: 'NH₃', min: 0, max: 10, step: 0.01, unit: 'mg/L' },
        { id: 'tss', label: 'TSS', min: 0, max: 200, step: 1, unit: 'mg/L' },
        { id: 'bod5', label: 'BOD₅', min: 0, max: 20, step: 0.1, unit: 'mg/L' },
    ],
    sediment: [
        { id: 'as', label: 'Arsenic (As)', min: 0, max: 50, step: 0.1, unit: 'mg/kg' },
        { id: 'cd', label: 'Cadmium (Cd)', min: 0, max: 5, step: 0.01, unit: 'mg/kg' },
        { id: 'pb', label: 'Lead (Pb)', min: 0, max: 100, step: 0.1, unit: 'mg/kg' },
        { id: 'cu', label: 'Copper (Cu)', min: 0, max: 150, step: 0.1, unit: 'mg/kg' },
        { id: 'zn', label: 'Zinc (Zn)', min: 0, max: 400, step: 1, unit: 'mg/kg' },
    ]
};

function CalculatorPage() {
    const [inputValues, setInputValues] = useState({});
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [csvFile, setCsvFile] = useState(null);
    const [csvResults, setCsvResults] = useState(null);

    const handleInputChange = (paramId, value) => {
        if (value === '' || isNaN(value)) {
            // Remove the key if empty
            const newValues = { ...inputValues };
            delete newValues[paramId];
            setInputValues(newValues);
        } else {
            setInputValues({ ...inputValues, [paramId]: parseFloat(value) });
        }
    };

    const clearAllInputs = () => {
        setInputValues({});
        setResult(null);
    };

    const calculateEAI = async () => {
        // Check if at least one input has a value
        if (Object.keys(inputValues).length === 0) {
            setResult({ error: 'Please enter at least one parameter value.' });
            return;
        }

        setLoading(true);
        try {
            const response = await api.post('/calculate-eai', {
                sample_type: 'MIXED',
                data: inputValues
            });
            setResult(response.data);
        } catch (error) {
            console.error('Error calculating EAI:', error);
            setResult({ error: 'Failed to calculate EAI. Please check your connection.' });
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
            formData.append('sample_type', 'MIXED');

            const response = await api.post('/calculate-eai-csv', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            setCsvResults(response.data);
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

    const filledCount = Object.keys(inputValues).length;
    const totalParams = ALL_PARAMS.waterQuality.length + ALL_PARAMS.sediment.length;

    return (
        <div className="calculator-page">
            <div className="calculator-header">
                <h2>EAI Calculator</h2>
                <p>Enter any environmental parameters to calculate the Environmental Alert Index. Only filled fields will be used in the calculation.</p>
            </div>

            <div className="calculator-content">
                {/* Manual Input Section */}
                <div className="input-section">
                    <div className="section-header">
                        <h3>Manual Input</h3>
                        <span className="input-count">{filledCount} of {totalParams} parameters filled</span>
                    </div>

                    {/* Water Quality Parameters */}
                    <div className="param-category">
                        <h4 className="category-title"> Water Quality Parameters</h4>
                        <div className="param-grid">
                            {ALL_PARAMS.waterQuality.map((param) => (
                                <div key={param.id} className={`param-input ${inputValues[param.id] !== undefined ? 'filled' : ''}`}>
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
                                        value={inputValues[param.id] ?? ''}
                                        onChange={(e) => handleInputChange(param.id, e.target.value)}
                                        placeholder={`${param.min} - ${param.max}`}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sediment Parameters */}
                    <div className="param-category">
                        <h4 className="category-title"> Sediment Parameters (Heavy Metals)</h4>
                        <div className="param-grid">
                            {ALL_PARAMS.sediment.map((param) => (
                                <div key={param.id} className={`param-input ${inputValues[param.id] !== undefined ? 'filled' : ''}`}>
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
                                        value={inputValues[param.id] ?? ''}
                                        onChange={(e) => handleInputChange(param.id, e.target.value)}
                                        placeholder={`${param.min} - ${param.max}`}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>

                    <div className="button-group">
                        <button
                            className="btn btn-secondary"
                            onClick={clearAllInputs}
                            disabled={filledCount === 0}
                        >
                            Clear All
                        </button>
                        <button
                            className="btn btn-primary calculate-btn"
                            onClick={calculateEAI}
                            disabled={loading || filledCount === 0}
                        >
                            {loading ? 'Calculating...' : 'Calculate EAI'}
                        </button>
                    </div>

                    {/* Manual Input Result */}
                    {result && !result.error && (
                        <div className={`result-card ${getStatusClass(result.status)}`}>
                            <div className="result-eai">{result.eai?.toFixed(1) || 'N/A'}</div>
                            <div className="result-status">{result.status_label?.vi || result.status}</div>
                            <div className="result-details">
                                <h4>Sub-Indices (from {Object.keys(result.sub_indices || {}).length} parameters):</h4>
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
                        Upload a CSV file with any of these columns:<br />
                        <strong>Water:</strong> ph, do_man, nhiet_do_nuoc, nh3, tss, bod5<br />
                        <strong>Sediment:</strong> as, cd, pb, cu, zn
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
