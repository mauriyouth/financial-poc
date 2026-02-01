import axios from 'axios';

export const API_BASE_URL = 'http://localhost:8000'; // Hardcoded for now, use env in prod

export const api = axios.create({
    baseURL: API_BASE_URL,
});
