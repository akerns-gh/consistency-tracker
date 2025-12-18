import axios from 'axios'
import { fetchAuthSession } from 'aws-amplify/auth'

// Get API endpoint from environment or use default
const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://api.repwarrior.net'

// Create Axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
api.interceptors.request.use(
  async (config) => {
    // Add auth token from Amplify if available
    try {
      const session = await fetchAuthSession()
      const token = session.tokens?.idToken?.toString()
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      } else {
        // If we're trying to access a protected endpoint but have no token, log it
        if (config.url && !config.url.includes('/login') && !config.url.includes('/public')) {
          console.warn('API request made without authentication token:', config.url)
        }
      }
    } catch (error) {
      // User not authenticated, continue without token
      // Only log if it's not a public endpoint
      if (config.url && !config.url.includes('/login') && !config.url.includes('/public')) {
        console.debug('No auth token available for:', config.url)
      }
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      // Handle specific error codes
      if (error.response.status === 401) {
        // Unauthorized - redirect to login
        // Token is managed by Amplify, no need to clear localStorage
        if (window.location.pathname !== '/login' && window.location.pathname !== '/admin/login') {
          window.location.href = '/login'
        }
      } else if (error.response.status === 403) {
        // Forbidden
        console.error('Access denied')
      } else if (error.response.status >= 500) {
        // Server error
        console.error('Server error:', error.response.data)
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network error:', error.request)
    } else {
      // Something else happened
      console.error('Error:', error.message)
    }
    return Promise.reject(error)
  }
)

export default api

