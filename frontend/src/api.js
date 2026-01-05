import axios from 'axios';

// Use /api prefix in production (Docker), direct URL in development
const API_BASE_URL = import.meta.env.PROD ? '/api' : 'http://localhost:8000';

const api = axios.create({
    baseURL: API_BASE_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

export const fetchRegions = async () => {
    const response = await api.get('/regions');
    return response.data;
};

export const fetchStations = async (region = null) => {
    const params = region ? { region } : {};
    const response = await api.get('/stations', { params });
    return response.data;
};

export const fetchEAI = async (filters = {}) => {
    const params = {};

    if (filters.region) params.region = filters.region;
    if (filters.station) params.station = filters.station;
    if (filters.sample_type) params.sample_type = filters.sample_type;
    if (filters.water_layer) params.water_layer = filters.water_layer;
    if (filters.start_date) params.start_date = filters.start_date;
    if (filters.end_date) params.end_date = filters.end_date;
    params.limit = filters.limit || 500;

    const response = await api.get('/eai', { params });
    return response.data;
};

export const fetchStatistics = async (filters = {}) => {
    const params = {};
    if (filters.region) params.region = filters.region;
    if (filters.station) params.station = filters.station;

    const response = await api.get('/statistics', { params });
    return response.data;
};

export default api;
