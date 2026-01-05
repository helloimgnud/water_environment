import { useState, useEffect } from 'react';

function FilterPanel({ filters, setFilters, onApply, regions, stations }) {
    // Check if station should be disabled (no region selected)
    const isStationDisabled = !filters.region;

    // Check if water layer should be disabled (sediment selected)
    const isWaterLayerDisabled = filters.sample_type === 'SEDIMENT';

    // Handle sample type change - clear water_layer if switching to SEDIMENT
    const handleSampleTypeChange = (e) => {
        const newType = e.target.value;
        if (newType === 'SEDIMENT') {
            setFilters({ ...filters, sample_type: newType, water_layer: '' });
        } else {
            setFilters({ ...filters, sample_type: newType });
        }
    };

    // Handle region change - clear station when region changes
    const handleRegionChange = (e) => {
        setFilters({ ...filters, region: e.target.value, station: '' });
    };

    return (
        <div className="filter-panel">
            <div className="filter-grid">
                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">Region</span>
                    </div>
                    <select
                        value={filters.region}
                        onChange={handleRegionChange}
                    >
                        <option value="">All Regions</option>
                        {regions.map((r) => (
                            <option key={r} value={r}>{r}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">Station</span>
                        {isStationDisabled && <span className="filter-hint">(select region first)</span>}
                    </div>
                    <select
                        value={filters.station}
                        onChange={(e) => setFilters({ ...filters, station: e.target.value })}
                        disabled={isStationDisabled}
                        className={isStationDisabled ? 'disabled' : ''}
                    >
                        <option value="">All Stations</option>
                        {stations.map((s) => (
                            <option key={s} value={s}>{s}</option>
                        ))}
                    </select>
                </div>

                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">Sample Type</span>
                    </div>
                    <select
                        value={filters.sample_type}
                        onChange={handleSampleTypeChange}
                    >
                        <option value="">All Types</option>
                        <option value="SEDIMENT">Sediment</option>
                        <option value="WATER_QUALITY">Water Quality</option>
                    </select>
                </div>

                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">Water Layer</span>
                        {isWaterLayerDisabled && <span className="filter-hint">(N/A for sediment)</span>}
                    </div>
                    <select
                        value={filters.water_layer}
                        onChange={(e) => setFilters({ ...filters, water_layer: e.target.value })}
                        disabled={isWaterLayerDisabled}
                        className={isWaterLayerDisabled ? 'disabled' : ''}
                    >
                        <option value="">All Layers</option>
                        <option value="SURFACE">Surface</option>
                        <option value="MIDDLE">Middle</option>
                        <option value="BOTTOM">Bottom</option>
                    </select>
                </div>

                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">Start Date</span>
                    </div>
                    <input
                        type="date"
                        value={filters.start_date}
                        onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
                    />
                </div>

                <div className="filter-group">
                    <div className="filter-label-container">
                        <span className="filter-label">End Date</span>
                    </div>
                    <input
                        type="date"
                        value={filters.end_date}
                        onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
                    />
                </div>

                <div className="filter-group filter-group-button">
                    <button className="btn btn-primary" onClick={onApply}>
                        Apply Filters
                    </button>
                </div>
            </div>
        </div>
    );
}

export default FilterPanel;
