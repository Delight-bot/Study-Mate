import axios from 'axios'
import { getSession, clearSession } from './auth'

// In dev, Vite proxies '/api' to the gateway (see vite.config.js), so this
// stays empty and requests go through the dev server.
// In a static build (e.g. GitHub Pages) there is no proxy, so requests must
// go straight to wherever the gateway is hosted. Set VITE_API_BASE_URL at
// build time to that URL, e.g.:
//   VITE_API_BASE_URL=https://your-gateway-host.example.com npm run build
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

const instance = axios.create({ baseURL })

instance.interceptors.request.use((config) => {
  const session = getSession()
  if (session?.token) {
    config.headers.Authorization = `Bearer ${session.token}`
  }
  return config
})

instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearSession()
      window.location.reload()
    }
    return Promise.reject(error)
  }
)

export default instance
