import axios from 'axios';

// Production is served behind the same-origin /api reverse proxy. Keep the
// localhost URL for the Vue development server only.
const RAW_API_BASE_URL = process.env.VUE_APP_API_BASE_URL
  || (process.env.NODE_ENV === 'production' ? '/api' : 'http://127.0.0.1:8000');
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, '');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export function toApiUrl(path) {
  if (!path) return '';
  if (/^https?:\/\//i.test(path)) return path;

  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalizedPath}`;
}

export default api;
