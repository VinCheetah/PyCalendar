import axios from 'axios'

// Instance Axios configurée pour l'API PyCalendar
const api = axios.create({
  baseURL: '/api',  // Proxy Vite redirigera vers http://localhost:8000
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000,  // 5 minutes timeout (pour les solvers CP-SAT qui peuvent être longs)
})

// Interceptor pour logging (optionnel, utile en dev)
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => {
    console.error('[API] Request error:', error)
    return Promise.reject(error)
  }
)

api.interceptors.response.use(
  (response) => {
    console.log(`[API] Response ${response.status} from ${response.config.url}`)
    return response
  },
  (error) => {
    console.error('[API] Response error:', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api
