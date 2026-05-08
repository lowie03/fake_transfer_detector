import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('tg_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

client.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('tg_token')
      localStorage.removeItem('tg_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default client
