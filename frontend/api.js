import axios from 'axios'

// In dev, Vite proxies '/api' to the gateway (see vite.config.js), so this
// stays empty and requests go through the dev server.
// In a static build (e.g. GitHub Pages) there is no proxy, so requests must
// go straight to wherever the gateway is hosted. Set VITE_API_BASE_URL at
// build time to that URL, e.g.:
//   VITE_API_BASE_URL=https://your-gateway-host.example.com npm run build
const baseURL = import.meta.env.VITE_API_BASE_URL || ''

export default axios.create({ baseURL })
