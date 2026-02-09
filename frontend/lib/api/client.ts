import axios from 'axios';

import { getApiBaseUrl } from '../config';

export const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
    baseURL: API_BASE_URL,
});
