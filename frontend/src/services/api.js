/**
 * API Service
 * 
 * Configured Axios instance for making API requests.
 * Handles authentication headers and error responses.
 */

import axios from 'axios'

// Create axios instance with base configuration
const api = axios.create({
  // In development, Vite proxies /api to backend
  // In production, this would be the full backend URL
  baseURL: '/api',
  timeout: 30000, // 30 second timeout
  headers: {
    'Content-Type': 'application/json',
  },
})

/**
 * Request interceptor
 * 
 * Adds authentication token to all requests if available.
 */
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')

    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor
 * 
 * Handles common error responses:
 * - 401: Redirect to login (token expired/invalid)
 * - Other errors: Pass through for component handling
 */
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid
      localStorage.removeItem('token')

      // Redirect to login if not already there
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }

    return Promise.reject(error)
  }
)

export default api
